"""
Dashboard Web — Painel de Controle de Segurança na Nuvem
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import threading
import time
import json
import os
import glob
from datetime import datetime
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__, template_folder="templates")
CORS(app)

# ── Configuração ───────────────────────────────────────────────────────────────
_VULN_CANDIDATES = [
    os.environ.get("VULN_URL", "").strip(),
    "http://api-vulneravel:5000",
    "http://localhost:8081",
]
_SECURE_CANDIDATES = [
    os.environ.get("SECURE_URL", "").strip(),
    "http://api-protegida:5000",
    "http://localhost:8082",
]

ALVOS = {
    "vuln":   {"candidates": _VULN_CANDIDATES,   "nome": "API Vulnerável", "_url": None},
    "secure": {"candidates": _SECURE_CANDIDATES, "nome": "API Protegida",  "_url": None},
}

WORDLIST_PATH = os.environ.get(
    "WORDLIST_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "atacante", "wordlist.txt"),
)
LOG_DIR = os.environ.get(
    "LOG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs"),
)

attack_queues  = {}
attack_results = {}
attack_status  = {}
_resolve_lock  = threading.Lock()


# ── URL Resolution ─────────────────────────────────────────────────────────────

def _probe(url, timeout=3):
    """Testa /health. Retorna (True, dados) ou (False, None)."""
    try:
        r = requests.get(f"{url}/health", timeout=timeout)
        if r.status_code == 200:
            return True, r.json()
    except Exception:
        pass
    return False, None


def get_url(key):
    """Retorna a URL funcional do alvo. Thread-safe."""
    info = ALVOS[key]
    if info["_url"]:
        ok, _ = _probe(info["_url"], timeout=2)
        if ok:
            return info["_url"]
        with _resolve_lock:
            info["_url"] = None

    with _resolve_lock:
        if info["_url"]:
            return info["_url"]
        for url in info["candidates"]:
            if not url:
                continue
            ok, _ = _probe(url, timeout=2)
            if ok:
                info["_url"] = url
                print(f"[RESOLVE] {key} -> {url}")
                return url
        fallback = next((u for u in info["candidates"] if u), "")
        info["_url"] = fallback
        return fallback


def api_status(key):
    """Uma única chamada HTTP por checagem de status."""
    info = ALVOS[key]
    candidates = []
    if info["_url"]:
        candidates = [info["_url"]] + [u for u in info["candidates"] if u and u != info["_url"]]
    else:
        candidates = [u for u in info["candidates"] if u]

    for url in candidates:
        ok, data = _probe(url, timeout=3)
        if ok:
            info["_url"] = url
            return {"online": True, "modo": data.get("modo", "OK"), "url": url}

    display_url = info["_url"] or next((u for u in info["candidates"] if u), "—")
    return {"online": False, "modo": "offline", "url": display_url}


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_wordlist():
    if not os.path.exists(WORDLIST_PATH):
        return []
    with open(WORDLIST_PATH, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def read_log(filename):
    path = os.path.join(LOG_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return [l.rstrip() for l in f.readlines()[-300:]]


def load_reports():
    os.makedirs(LOG_DIR, exist_ok=True)
    out = []
    for fp in sorted(glob.glob(os.path.join(LOG_DIR, "ataque_*.json")), reverse=True)[:30]:
        try:
            with open(fp, encoding="utf-8") as f:
                d = json.load(f)
            d["_filename"] = os.path.basename(fp)
            out.append(d)
        except Exception:
            pass
    return out


def save_report(data, tipo, alvo_key):
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"ataque_{tipo}_{alvo_key}_{ts}.json"
    with open(os.path.join(LOG_DIR, fname), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return fname


# ── Brute Force ────────────────────────────────────────────────────────────────

def run_bruteforce(attack_id, alvo_key, max_tentativas):
    q        = attack_queues[attack_id]
    nome     = ALVOS[alvo_key]["nome"]
    base_url = get_url(alvo_key)
    senhas   = load_wordlist()[:max_tentativas]

    q.put({"type": "info", "msg": f"Iniciando Brute Force contra {nome}"})
    q.put({"type": "info", "msg": f"Alvo: {base_url}/login | Wordlist: {len(senhas)} senhas"})

    result = {
        "tipo_ataque": "bruteforce",
        "alvo": nome, "alvo_key": alvo_key,
        "inicio": datetime.now().isoformat(),
        "total_tentativas": 0,
        "senha_encontrada": None,
        "tentativas": [],
        "estatisticas": {},
    }
    codigos = {}

    for i, senha in enumerate(senhas, 1):
        try:
            t0   = time.time()
            r    = requests.post(f"{base_url}/login",
                                 json={"username": "admin", "password": senha},
                                 timeout=10)
            tempo = round(time.time() - t0, 3)
            code  = r.status_code
            codigos[code] = codigos.get(code, 0) + 1
            result["tentativas"].append({"numero": i, "senha": senha,
                                         "status_code": code, "tempo": tempo})
            result["total_tentativas"] = i

            color = "success" if code == 200 else ("blocked" if code == 429 else "fail")
            q.put({"type": "attempt", "numero": i, "total": len(senhas),
                   "senha": senha, "code": code, "tempo": tempo, "color": color})

            if code == 200:
                result["senha_encontrada"] = senha
                q.put({"type": "found", "msg": f"SENHA ENCONTRADA: '{senha}' (tentativa #{i})"})
                break
            elif code == 429:
                q.put({"type": "blocked", "msg": f"IP bloqueado (429) apos {i} tentativa(s)."})
                break

        except Exception as e:
            q.put({"type": "error", "msg": f"Erro na tentativa {i}: {str(e)}"})

    result["fim"] = datetime.now().isoformat()
    dt = (datetime.fromisoformat(result["fim"])
          - datetime.fromisoformat(result["inicio"])).total_seconds()
    result["estatisticas"] = {"codigos_http": codigos, "tempo_total": round(dt, 2)}

    fname = save_report(result, "bruteforce", alvo_key)
    q.put({"type": "done", "result": result, "filename": fname})
    attack_results[attack_id] = result
    attack_status[attack_id]  = "done"


# ── DoS (threads síncronas — sem aiohttp) ─────────────────────────────────────

def _dos_worker(url, resultados, lock, fim_flag, session):
    """Worker síncrono do DoS. Roda em thread separada."""
    while not fim_flag[0]:
        t0 = time.time()
        try:
            r = session.get(url, timeout=8)
            tempo = round(time.time() - t0, 3)
            with lock:
                resultados.append({"status_code": r.status_code, "tempo": tempo,
                                   "erro": False})
        except requests.exceptions.ConnectionError:
            tempo = round(time.time() - t0, 3)
            with lock:
                resultados.append({"status_code": 0, "tempo": tempo,
                                   "erro": True, "tipo_erro": "refused"})
        except requests.exceptions.Timeout:
            tempo = round(time.time() - t0, 3)
            with lock:
                resultados.append({"status_code": 0, "tempo": tempo,
                                   "erro": True, "tipo_erro": "timeout"})
        except Exception as e:
            tempo = round(time.time() - t0, 3)
            with lock:
                resultados.append({"status_code": 0, "tempo": tempo,
                                   "erro": True, "tipo_erro": "erro"})


def run_dos(attack_id, alvo_key, workers, duracao):
    q        = attack_queues[attack_id]
    nome     = ALVOS[alvo_key]["nome"]
    base_url = get_url(alvo_key)
    url      = f"{base_url}/relatorio"

    q.put({"type": "info", "msg": f"Iniciando DoS contra {nome}"})
    q.put({"type": "info", "msg": f"Alvo: {url} | Workers: {workers} | Duracao: {duracao}s"})

    # Verifica acessibilidade antes de começar
    ok, _ = _probe(base_url, timeout=4)
    if not ok:
        q.put({"type": "error",
               "msg": f"API nao responde em {base_url}. Aguarde e tente novamente."})
        result = {
            "tipo_ataque": "dos", "alvo": nome, "alvo_key": alvo_key,
            "config": {"workers": workers, "duracao_segundos": duracao},
            "estatisticas": {
                "total_requisicoes": 0, "codigos_http": {},
                "erros_timeouts": 0, "erros_recusados": 0, "outros_erros": 0,
                "tempo_resposta_medio": 0, "tempo_resposta_p95": 0,
                "aviso": "API indisponivel no inicio do ataque",
            },
        }
        fname = save_report(result, "dos", alvo_key)
        q.put({"type": "done", "result": result, "filename": fname})
        attack_results[attack_id] = result
        attack_status[attack_id]  = "done"
        return

    resultados = []
    lock       = threading.Lock()
    fim_flag   = [False]

    # Cria uma sessão requests por worker para reusar conexões
    sessions = [requests.Session() for _ in range(workers)]

    # Inicia threads
    threads = []
    for i in range(workers):
        t = threading.Thread(
            target=_dos_worker,
            args=(url, resultados, lock, fim_flag, sessions[i]),
            daemon=True,
        )
        t.start()
        threads.append(t)

    # Loop de monitoramento
    t_inicio = time.time()
    while time.time() - t_inicio < duracao:
        time.sleep(2)
        elapsed = round(time.time() - t_inicio, 1)
        with lock:
            total = len(resultados)
            cp = {}
            for r in resultados:
                c = r["status_code"]
                cp[c] = cp.get(c, 0) + 1
        q.put({"type": "dos_progress", "elapsed": elapsed, "duracao": duracao,
               "total": total, "codigos": cp})

    # Para workers
    fim_flag[0] = True
    for s in sessions:
        try:
            s.close()
        except Exception:
            pass
    for t in threads:
        t.join(timeout=1)

    # Estatísticas finais
    with lock:
        snap = list(resultados)

    codigos = {}
    tempos  = []
    timeouts = refused = outros_err = 0

    for r in snap:
        c = r["status_code"]
        codigos[c] = codigos.get(c, 0) + 1
        tempos.append(r["tempo"])
        if r.get("erro"):
            tipo = r.get("tipo_erro", "erro")
            if   tipo == "timeout": timeouts   += 1
            elif tipo == "refused": refused    += 1
            else:                   outros_err += 1

    tempos.sort()
    avg = round(sum(tempos) / len(tempos), 4) if tempos else 0
    p95 = round(tempos[int(len(tempos) * 0.95)], 4) if tempos else 0

    result = {
        "tipo_ataque": "dos", "alvo": nome, "alvo_key": alvo_key,
        "config": {"workers": workers, "duracao_segundos": duracao},
        "estatisticas": {
            "total_requisicoes": len(snap),
            "codigos_http": codigos,
            "erros_timeouts": timeouts,
            "erros_recusados": refused,
            "outros_erros": outros_err,
            "tempo_resposta_medio": avg,
            "tempo_resposta_p95": p95,
        },
    }

    fname = save_report(result, "dos", alvo_key)
    q.put({"type": "done", "result": result, "filename": fname})
    attack_results[attack_id] = result
    attack_status[attack_id]  = "done"


# ── Rotas ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/api/status")
def route_status():
    reports = load_reports()
    return jsonify({
        "vuln":          api_status("vuln"),
        "secure":        api_status("secure"),
        "wordlist_size": len(load_wordlist()),
        "bf_count":      sum(1 for r in reports if r.get("tipo_ataque") == "bruteforce"),
        "dos_count":     sum(1 for r in reports if r.get("tipo_ataque") == "dos"),
    })


@app.route("/api/reports")
def route_reports():
    return jsonify(load_reports())


@app.route("/api/logs/<filename>")
def route_logs(filename):
    allowed = {"gateway.log", "api_vulneravel.log", "api_protegida.log"}
    if filename not in allowed:
        return jsonify({"error": "Nao permitido"}), 403
    return jsonify({"lines": read_log(filename)})


@app.route("/api/attack/start", methods=["POST"])
def route_start():
    data = request.json or {}
    tipo = data.get("tipo")
    alvo = data.get("alvo")
    if tipo not in ("bruteforce", "dos") or alvo not in ("vuln", "secure"):
        return jsonify({"error": "Parametros invalidos"}), 400

    attack_id = f"{tipo}_{alvo}_{int(time.time()*1000)}"
    attack_queues[attack_id] = queue.Queue()
    attack_status[attack_id] = "running"

    if tipo == "bruteforce":
        max_t = int(data.get("max_tentativas", 50))
        t = threading.Thread(target=run_bruteforce, args=(attack_id, alvo, max_t), daemon=True)
    else:
        w = int(data.get("workers", 20))
        d = int(data.get("duracao", 15))
        t = threading.Thread(target=run_dos, args=(attack_id, alvo, w, d), daemon=True)

    t.start()
    return jsonify({"attack_id": attack_id})


@app.route("/api/attack/poll/<attack_id>")
def route_poll(attack_id):
    if attack_id not in attack_queues:
        return jsonify({"error": "ID invalido"}), 404
    events = []
    try:
        while True:
            events.append(attack_queues[attack_id].get_nowait())
    except queue.Empty:
        pass
    return jsonify({"events": events, "status": attack_status.get(attack_id, "unknown")})


@app.route("/api/direct/<alvo>/<path:endpoint>", methods=["GET", "POST"])
def route_direct(alvo, endpoint):
    if alvo not in ALVOS:
        return jsonify({"error": "Alvo invalido"}), 400
    url = get_url(alvo)
    if not url:
        return jsonify({"error": "API nao disponivel"}), 503
    try:
        r = requests.request(
            method=request.method,
            url=f"{url}/{endpoint}",
            json=request.get_json(silent=True),
            timeout=10,
        )
        return jsonify({"status_code": r.status_code, "body": r.json()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=== Dashboard de Seguranca — http://localhost:5050 ===")
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)