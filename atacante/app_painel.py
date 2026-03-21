from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)

# URL alvo (Gateway exposto pelo Docker)
TARGET_URL = "http://gateway:5000"

def thread_ataque_generic(method, endpoint, quantidade, payload=None):
    """Thread genérica para executar requisições em repetição"""
    url_completa = f"{TARGET_URL}{endpoint}"
    
    for i in range(int(quantidade)):
        try:
            if method.upper() == "GET":
                requests.get(url_completa, timeout=5)
            elif method.upper() == "POST":
                # Se for força bruta, envia o índice como senha simulada
                if endpoint == "/login" and payload:
                    current_payload = payload.copy()
                    current_payload['pass'] = f"senha_{i}" # Simula senhas diferentes
                    requests.post(url_completa, json=current_payload, timeout=5)
                else:
                    requests.post(url_completa, json=payload, timeout=5)
            
            # Pequeno delay para não sobrecarregar instantaneamente o gateway
            # e permitir que os logs sejam gerados em ordem legível
            time.sleep(0.05) 
            
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {url_completa}: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/disparar', methods=['POST'])
def disparar():
    dados = request.json
    tipo = dados.get('tipo')
    qtd = dados.get('quantidade', 5)
    
    method = "GET"
    endpoint = "/"
    payload = None

    # Mapeamento de tipos de ataque para configurações reais
    if tipo == "users":
        endpoint = "/users"
    elif tipo == "admin":
        endpoint = "/admin"
    elif tipo == "forca_bruta":
        method = "POST"
        endpoint = "/login"
        payload = {"user": "admin", "pass": "temp"} # Senha será alterada na thread
    else:
        return jsonify({"status": "erro", "mensagem": "Tipo de ataque desconhecido"}), 400

    # Dispara a thread para não travar a UI
    thread = threading.Thread(target=thread_ataque_generic, args=(method, endpoint, qtd, payload))
    thread.start()
    
    return jsonify({"status": "iniciado", "tipo": tipo, "quantidade": qtd})

@app.route('/obter_logs')
def obter_logs():
    # Caminho para os logs (considerando o volume compartilhado no Docker)
    is_docker = os.path.exists('/.dockerenv')
    log_dir = '/logs' if is_docker else './logs'
    
    try:
        with open(f"{log_dir}/gateway.log", "r") as f:
            # Pega as últimas 10 linhas para não sobrecarregar a tela
            linhas = f.readlines()[-10:]
            return jsonify({"status": "sucesso", "logs": linhas})
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)})

if __name__ == "__main__":
    # Roda na porta 8080 para não conflitar com o Gateway (5000)
    app.run(host="0.0.0.0", port=8080)