from flask import Flask, request, jsonify
import logging
import os

app = Flask(__name__)

# Detectar se está rodando em Docker
is_docker = os.path.exists('/.dockerenv')
log_dir = '/logs' if is_docker else './logs'

os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=f'{log_dir}/api.log', level=logging.INFO, encoding='utf-8')

@app.route("/data")
def data():
    logging.info("endpoint /data accessed")
    return jsonify({"status": "ok", "data": "public data"})

@app.route("/admin")
def admin():
    logging.info("admin endpoint accessed")
    return jsonify({"status": "forbidden"}), 403

app.run(host="0.0.0.0", port=5000) #se usar localmente, mude para 5001 para evitar conflito com o gateway que roda na 5000