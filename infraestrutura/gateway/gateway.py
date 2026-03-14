from flask import Flask, request, jsonify
import requests
import logging
import os

app = Flask(__name__)

# Criando diretório de logs se não existir
os.makedirs('/logs', exist_ok=True)

# Configurando logging para o gateway
logging.basicConfig(filename='/logs/gateway.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL da API interna
API_BASE_URL = "http://api:5000"

@app.route("/data")
def data():
    try:
        # Encaminhar requisição para a API
        response = requests.get(f"{API_BASE_URL}/data")
        logging.info(f"Requisição para /data - Status: {response.status_code}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Erro ao acessar /data: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/admin")
def admin():
    try:
        # Encaminhar requisição para a API
        response = requests.get(f"{API_BASE_URL}/admin")
        logging.info(f"Requisição para /admin - Status: {response.status_code}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Erro ao acessar /admin: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)