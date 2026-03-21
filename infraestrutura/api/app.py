from flask import Flask, request, jsonify
import logging
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Detectar se está rodando em Docker
is_docker = os.path.exists('/.dockerenv')
log_dir = '/logs' if is_docker else './logs'

os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=f'{log_dir}/api.log', level=logging.INFO, encoding='utf-8')

# Configuração do banco de dados
DATABASE_URL = "postgresql://user:password@database:5432/mydb" if is_docker else "postgresql://user:password@localhost:5432/mydb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    public = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

@app.route("/data")
def data():
    logging.info("endpoint /data accessed")
    return jsonify({"status": "ok", "data": "public data"})

@app.route("/users")
def users():
    db = get_db()
    public_users = db.query(User).filter(User.public == True).all()
    users_list = [{"id": u.id, "name": u.name} for u in public_users]
    logging.info("endpoint /users accessed")
    return jsonify({"status": "ok", "users": users_list})

@app.route("/admin")
def admin():
    logging.info("admin endpoint accessed")
    return jsonify({"status": "forbidden"}), 403

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("user")
    password = data.get("pass")
    
    logging.info(f"Tentativa de login para o usuário: {username}")
    
    # Simulação de verificação de senha
    if username == "admin" and password == "admin123":
        logging.info(f"Login bem-sucedido para: {username}")
        return jsonify({"status": "success", "message": "Bem-vindo, admin!"}), 200
    else:
        logging.warning(f"Falha de login para: {username} com a senha: {password}")
        return jsonify({"status": "error", "message": "Credenciais inválidas"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000) #se usar localmente, mude para 5001 para evitar conflito com o gateway que roda na 5000