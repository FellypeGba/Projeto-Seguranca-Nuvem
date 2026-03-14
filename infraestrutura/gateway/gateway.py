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

# Rota Genérica para proxy de requisições para a API
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    try:
        url = f"{API_BASE_URL}/{path}"
        response = requests.request(
            method=request.method,
            url=url,
            json=request.get_json(silent=True),
            params=request.args
        )
        logging.info(f"Requisição para /{path} - Método: {request.method} - Status: {response.status_code}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Erro ao acessar /{path}: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)