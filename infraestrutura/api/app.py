from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
import time
import bcrypt
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

app = FastAPI(title="API Nuvem", description="Simulação de API em ambiente de nuvem")

# ── Configuração ──────────────────────────────────────────────────────────────
MODO_PROTEGIDO = os.environ.get("MODO_PROTEGIDO", "False").lower() in ("true", "1", "yes")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/mydb")
MODO_LABEL = "PROTEGIDA" if MODO_PROTEGIDO else "VULNERÁVEL"

# ── Logging ───────────────────────────────────────────────────────────────────
is_docker = os.path.exists("/.dockerenv")
log_dir = "/logs" if is_docker else "./logs"
os.makedirs(log_dir, exist_ok=True)

log_suffix = "protegida" if MODO_PROTEGIDO else "vulneravel"
logging.basicConfig(
    filename=f"{log_dir}/api_{log_suffix}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

# ── Banco de dados ────────────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)


class RegistroRelatorio(Base):
    __tablename__ = "registros_relatorio"
    id = Column(Integer, primary_key=True, index=True)
    data_transacao = Column(DateTime, nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    descricao = Column(Text, nullable=False)
    categoria = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)

class LoginRequest(BaseModel):
    username: str
    password: str

# ── Proteções (rate limiting / bloqueio por IP) ───────────────────────────────
login_falhas = {}  # {ip: {"contagem": int, "bloqueado_ate": float}}
relatorio_requests = {}  # {ip: [timestamp, ...]}

MAX_TENTATIVAS_LOGIN = 3
BLOQUEIO_SEGUNDOS = 60
MAX_RELATORIO_POR_SEGUNDO = 2


def ip_bloqueado_login(ip):
    """Verifica se o IP está bloqueado para login (modo protegido)."""
    if ip not in login_falhas:
        return False
    info = login_falhas[ip]
    if info.get("bloqueado_ate") and time.time() < info["bloqueado_ate"]:
        return True
    if info.get("bloqueado_ate") and time.time() >= info["bloqueado_ate"]:
        login_falhas[ip] = {"contagem": 0, "bloqueado_ate": None}
    return False


def registrar_falha_login(ip):
    """Registra uma tentativa falha de login e bloqueia se exceder o limite."""
    if ip not in login_falhas:
        login_falhas[ip] = {"contagem": 0, "bloqueado_ate": None}
    login_falhas[ip]["contagem"] += 1
    if login_falhas[ip]["contagem"] >= MAX_TENTATIVAS_LOGIN:
        login_falhas[ip]["bloqueado_ate"] = time.time() + BLOQUEIO_SEGUNDOS
        logging.warning(f"IP {ip} bloqueado por {BLOQUEIO_SEGUNDOS}s após {MAX_TENTATIVAS_LOGIN} tentativas falhas")


def rate_limit_relatorio(ip):
    """Verifica se o IP excedeu o rate limit para /relatorio (modo protegido)."""
    agora = time.time()
    if ip not in relatorio_requests:
        relatorio_requests[ip] = []
    relatorio_requests[ip] = [t for t in relatorio_requests[ip] if agora - t < 1.0]
    if len(relatorio_requests[ip]) >= MAX_RELATORIO_POR_SEGUNDO:
        return True
    relatorio_requests[ip].append(agora)
    return False


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "modo": MODO_LABEL}


@app.post("/login")
async def login(request: Request, dados: LoginRequest):
    inicio = time.time()
    ip = request.client.host if request.client else "127.0.0.1"

    username = dados.username
    password = dados.password

    # ── Proteção: bloqueio por IP após falhas (só no modo protegido) ──
    if MODO_PROTEGIDO and ip_bloqueado_login(ip):
        tempo = round(time.time() - inicio, 4)
        logging.info(f"[LOGIN] IP={ip} user={username} - BLOQUEADO (429) - {tempo}s")
        return JSONResponse(status_code=429, content={"erro": "Muitas tentativas. Tente novamente mais tarde."})

    # ── Verificar credenciais no banco ──
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.username == username).first()
        if usuario and bcrypt.checkpw(password.encode("utf-8"), usuario.password_hash.encode("utf-8")):
            tempo = round(time.time() - inicio, 4)
            logging.info(f"[LOGIN] IP={ip} user={username} - SUCESSO (200) - {tempo}s")
            if ip in login_falhas:
                login_falhas[ip] = {"contagem": 0, "bloqueado_ate": None}
            return JSONResponse(status_code=200, content={"mensagem": "Login bem-sucedido", "usuario": username})
        else:
            if MODO_PROTEGIDO:
                registrar_falha_login(ip)
            tempo = round(time.time() - inicio, 4)
            logging.info(f"[LOGIN] IP={ip} user={username} - FALHA (401) - {tempo}s")
            return JSONResponse(status_code=401, content={"erro": "Credenciais inválidas"})
    finally:
        db.close()


@app.get("/relatorio")
def relatorio(request: Request):
    inicio = time.time()
    ip = request.client.host if request.client else "127.0.0.1"

    # ── Proteção: rate limiting (só no modo protegido) ──
    if MODO_PROTEGIDO and rate_limit_relatorio(ip):
        tempo = round(time.time() - inicio, 4)
        logging.info(f"[RELATORIO] IP={ip} - RATE LIMITED (429) - {tempo}s")
        return JSONResponse(status_code=429, content={"erro": "Limite de requisições excedido. Tente novamente em instantes."})

    # ── Query pesada: busca todos os registros sem paginação ──
    db = SessionLocal()
    try:
        registros = db.query(RegistroRelatorio).order_by(
            RegistroRelatorio.data_transacao,
            RegistroRelatorio.valor
        ).all()

        resultado = [
            {
                "id": r.id,
                "data": str(r.data_transacao),
                "valor": float(r.valor),
                "descricao": r.descricao,
                "categoria": r.categoria,
                "status": r.status,
            }
            for r in registros
        ]
        tempo = round(time.time() - inicio, 4)
        logging.info(f"[RELATORIO] IP={ip} - OK (200) - {len(resultado)} registros - {tempo}s")
        return JSONResponse(status_code=200, content={"total": len(resultado), "registros": resultado})
    except Exception as e:
        tempo = round(time.time() - inicio, 4)
        logging.error(f"[RELATORIO] IP={ip} - ERRO (500) - {str(e)} - {tempo}s")
        return JSONResponse(status_code=500, content={"erro": "Erro interno ao gerar relatório"})
    finally:
        db.close()


if __name__ == "__main__":
    print(f"=== API [{MODO_LABEL}] iniciando nativamente com uvicorn na porta 5000 ===")
    uvicorn.run("app:app", host="0.0.0.0", port=5000)