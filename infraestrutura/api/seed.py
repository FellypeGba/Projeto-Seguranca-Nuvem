"""
Script de inicialização (Migration + Seed).
Executado pelo entrypoint.sh antes da API iniciar.
Cria tabelas e popula o banco com dados fictícios.
"""

import os
import sys
import time
import random
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/mydb")

CATEGORIAS = ["vendas", "compras", "transferencias", "pagamentos", "estornos", "taxas", "investimentos", "saques"]
STATUS_OPCOES = ["concluido", "pendente", "cancelado", "processando", "erro"]
DESCRICAO_BASE = (
    "Transação referente a operação financeira registrada no sistema de controle interno. "
    "Este registro contém informações detalhadas sobre movimentações e processos internos "
    "que devem ser auditados periodicamente conforme política de segurança vigente."
)

TOTAL_REGISTROS = 100_000
BATCH_SIZE = 5_000


def aguardar_banco(engine, tentativas=30, intervalo=2):
    """Aguarda o banco de dados ficar disponível."""
    for i in range(tentativas):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✓ Banco de dados disponível.")
            return True
        except Exception:
            print(f"  Aguardando banco de dados... ({i + 1}/{tentativas})")
            time.sleep(intervalo)
    print("✗ Banco de dados não ficou disponível a tempo.")
    sys.exit(1)


def seed_usuarios(engine):
    """Insere usuários no banco (admin + comuns)."""
    with engine.connect() as conn:
        # Verificar se já existem usuários
        resultado = conn.execute(text("SELECT COUNT(*) FROM usuarios"))
        count = resultado.scalar()
        if count > 0:
            print(f"  Tabela 'usuarios' já possui {count} registros. Pulando seed.")
            return

        # Gerar hash da senha do admin
        senha_admin = bcrypt.hashpw("senha_secreta".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Inserir admin
        conn.execute(
            text("INSERT INTO usuarios (username, password_hash) VALUES (:u, :p)"),
            {"u": "admin", "p": senha_admin},
        )

        # Inserir usuários comuns
        usuarios_comuns = ["alice", "bob", "carlos", "diana", "eduardo"]
        for nome in usuarios_comuns:
            senha_hash = bcrypt.hashpw(f"senha_{nome}".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            conn.execute(
                text("INSERT INTO usuarios (username, password_hash) VALUES (:u, :p)"),
                {"u": nome, "p": senha_hash},
            )

        conn.commit()
        print(f"  ✓ {1 + len(usuarios_comuns)} usuários inseridos (admin + comuns).")


def seed_registros(engine):
    """Insere 100.000 registros na tabela registros_relatorio."""
    with engine.connect() as conn:
        # Verificar se já existem registros
        resultado = conn.execute(text("SELECT COUNT(*) FROM registros_relatorio"))
        count = resultado.scalar()
        if count > 0:
            print(f"  Tabela 'registros_relatorio' já possui {count} registros. Pulando seed.")
            return

        print(f"  Inserindo {TOTAL_REGISTROS} registros em batches de {BATCH_SIZE}...")
        data_inicio = datetime(2020, 1, 1)
        data_fim = datetime(2025, 12, 31)
        delta_total = (data_fim - data_inicio).days

        inseridos = 0
        inicio = time.time()

        for batch_num in range(TOTAL_REGISTROS // BATCH_SIZE):
            registros = []
            for _ in range(BATCH_SIZE):
                data = data_inicio + timedelta(days=random.randint(0, delta_total), seconds=random.randint(0, 86400))
                registros.append({
                    "data_transacao": data,
                    "valor": round(random.uniform(1.00, 99999.99), 2),
                    "descricao": DESCRICAO_BASE + f" Ref: {random.randint(100000, 999999)}",
                    "categoria": random.choice(CATEGORIAS),
                    "status": random.choice(STATUS_OPCOES),
                })

            conn.execute(
                text(
                    "INSERT INTO registros_relatorio (data_transacao, valor, descricao, categoria, status) "
                    "VALUES (:data_transacao, :valor, :descricao, :categoria, :status)"
                ),
                registros,
            )
            conn.commit()
            inseridos += BATCH_SIZE
            elapsed = round(time.time() - inicio, 1)
            print(f"    Batch {batch_num + 1}/{TOTAL_REGISTROS // BATCH_SIZE} — {inseridos}/{TOTAL_REGISTROS} ({elapsed}s)")

        total_time = round(time.time() - inicio, 1)
        print(f"  ✓ {TOTAL_REGISTROS} registros inseridos em {total_time}s.")


def main():
    print("=" * 60)
    print("SEED: Iniciando migração e carga de dados...")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    aguardar_banco(engine)

    with engine.connect() as conn:
        # PostgreSQL advisory lock to prevent concurrent seeding by two containers
        result = conn.execute(text("SELECT pg_try_advisory_lock(987654321)"))
        locked = result.scalar()
        
        if not locked:
            print("=> Outro container já iniciou o seed simultaneamente. Pulando...")
            # Wait a few seconds to let the other container finish its inserts before we boot the API
            time.sleep(5)
            return

        try:
            print("\n[1/2] Seed de usuários...")
            seed_usuarios(engine)

            print("\n[2/2] Seed de registros de relatório...")
            seed_registros(engine)

            print("\n" + "=" * 60)
            print("SEED: Concluído com sucesso!")
            print("=" * 60)
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(987654321)"))


if __name__ == "__main__":
    main()
