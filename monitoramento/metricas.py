"""
Módulo de monitoramento e comparação de resultados.

Lê os relatórios JSON gerados pelo atacar.py e produz
uma análise comparativa entre api-vulneravel e api-protegida.

Uso:
    python metricas.py

Saída:
    logs/comparativo.json
    logs/comparativo.csv
"""

import csv
import json
import os
import glob
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")


def carregar_relatorios(tipo_ataque):
    """Carrega os relatórios JSON mais recentes para cada alvo (vuln/secure)."""
    pattern = os.path.join(LOG_DIR, f"ataque_{tipo_ataque}_*.json")
    arquivos = glob.glob(pattern)

    resultados = {"vuln": None, "secure": None}
    for arq in sorted(arquivos, reverse=True):
        basename = os.path.basename(arq)
        if "vuln" in basename and resultados["vuln"] is None:
            with open(arq, "r", encoding="utf-8") as f:
                resultados["vuln"] = json.load(f)
        elif "secure" in basename and resultados["secure"] is None:
            with open(arq, "r", encoding="utf-8") as f:
                resultados["secure"] = json.load(f)
        if resultados["vuln"] and resultados["secure"]:
            break

    return resultados


def comparar_bruteforce(vuln, secure):
    """Compara resultados de brute force entre apis."""
    comparativo = {
        "tipo": "bruteforce",
        "timestamp": datetime.now().isoformat(),
        "api_vulneravel": {},
        "api_protegida": {},
        "conclusao": "",
    }

    if vuln:
        stats = vuln.get("estatisticas", {})
        codigos = stats.get("codigos_http", {})
        comparativo["api_vulneravel"] = {
            "total_tentativas": vuln.get("total_tentativas", 0),
            "senha_encontrada": vuln.get("senha_encontrada"),
            "codigos_http": codigos,
            "tempo_total": stats.get("tempo_total", 0),
            "bloqueios_429": codigos.get("429", codigos.get(429, 0)),
        }

    if secure:
        stats = secure.get("estatisticas", {})
        codigos = stats.get("codigos_http", {})
        comparativo["api_protegida"] = {
            "total_tentativas": secure.get("total_tentativas", 0),
            "senha_encontrada": secure.get("senha_encontrada"),
            "codigos_http": codigos,
            "tempo_total": stats.get("tempo_total", 0),
            "bloqueios_429": codigos.get("429", codigos.get(429, 0)),
        }

    # Conclusão
    vuln_encontrou = comparativo["api_vulneravel"].get("senha_encontrada") is not None
    secure_encontrou = comparativo["api_protegida"].get("senha_encontrada") is not None
    secure_bloqueou = comparativo["api_protegida"].get("bloqueios_429", 0) > 0

    if vuln_encontrou and not secure_encontrou and secure_bloqueou:
        comparativo["conclusao"] = (
            "A API vulnerável permitiu o brute force até encontrar a senha. "
            "A API protegida bloqueou o atacante após poucas tentativas (429 Too Many Requests)."
        )
    elif vuln_encontrou and secure_encontrou:
        comparativo["conclusao"] = (
            "Ambas as APIs permitiram o brute force. A proteção pode não estar funcionando corretamente."
        )
    else:
        comparativo["conclusao"] = "Análise inconclusiva - verifique se ambos os ataques foram executados."

    return comparativo


def comparar_dos(vuln, secure):
    """Compara resultados de DoS entre apis."""
    comparativo = {
        "tipo": "dos",
        "timestamp": datetime.now().isoformat(),
        "api_vulneravel": {},
        "api_protegida": {},
        "conclusao": "",
    }

    if vuln:
        stats = vuln.get("estatisticas", {})
        codigos = stats.get("codigos_http", {})
        comparativo["api_vulneravel"] = {
            "total_requisicoes": stats.get("total_requisicoes", 0),
            "codigos_http": codigos,
            "erros_timeouts": stats.get("erros_timeouts", 0),
            "tempo_resposta_medio": stats.get("tempo_resposta_medio", 0),
            "tempo_resposta_p95": stats.get("tempo_resposta_p95", 0),
            "requisicoes_sucesso_200": codigos.get("200", codigos.get(200, 0)),
            "bloqueios_429": codigos.get("429", codigos.get(429, 0)),
        }

    if secure:
        stats = secure.get("estatisticas", {})
        codigos = stats.get("codigos_http", {})
        comparativo["api_protegida"] = {
            "total_requisicoes": stats.get("total_requisicoes", 0),
            "codigos_http": codigos,
            "erros_timeouts": stats.get("erros_timeouts", 0),
            "tempo_resposta_medio": stats.get("tempo_resposta_medio", 0),
            "tempo_resposta_p95": stats.get("tempo_resposta_p95", 0),
            "requisicoes_sucesso_200": codigos.get("200", codigos.get(200, 0)),
            "bloqueios_429": codigos.get("429", codigos.get(429, 0)),
        }

    # Conclusão
    vuln_erros = comparativo["api_vulneravel"].get("erros_timeouts", 0)
    secure_bloqueios = comparativo["api_protegida"].get("bloqueios_429", 0)
    secure_erros = comparativo["api_protegida"].get("erros_timeouts", 0)

    if vuln_erros > 0 and secure_bloqueios > 0 and secure_erros <= vuln_erros:
        comparativo["conclusao"] = (
            f"A API vulnerável sofreu {vuln_erros} erros/timeouts sob ataque DoS. "
            f"A API protegida bloqueou {secure_bloqueios} requisições via rate limiting (429), "
            f"preservando a estabilidade da infraestrutura."
        )
    elif secure_bloqueios > 0:
        comparativo["conclusao"] = (
            f"A API protegida bloqueou {secure_bloqueios} requisições com rate limiting. "
            f"A API vulnerável processou todas as requisições sem proteção."
        )
    else:
        comparativo["conclusao"] = "Análise inconclusiva - verifique se ambos os ataques foram executados."

    return comparativo


def salvar_comparativo(dados, nome):
    """Salva comparativo em JSON e CSV."""
    os.makedirs(LOG_DIR, exist_ok=True)

    # JSON
    json_path = os.path.join(LOG_DIR, f"{nome}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    print(f"  📄 JSON: {json_path}")

    # CSV
    csv_path = os.path.join(LOG_DIR, f"{nome}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Métrica", "API Vulnerável", "API Protegida"])

        vuln_data = dados.get("api_vulneravel", {})
        secure_data = dados.get("api_protegida", {})

        all_keys = set(list(vuln_data.keys()) + list(secure_data.keys()))
        for key in sorted(all_keys):
            if key == "codigos_http":
                writer.writerow([key, json.dumps(vuln_data.get(key, {})), json.dumps(secure_data.get(key, {}))])
            else:
                writer.writerow([key, vuln_data.get(key, "N/A"), secure_data.get(key, "N/A")])

        writer.writerow(["conclusao", dados.get("conclusao", ""), ""])

    print(f"  📄 CSV:  {csv_path}")


def main():
    print("=" * 60)
    print("  MONITORAMENTO - Comparativo de Ataques")
    print("=" * 60)

    # Brute Force
    print("\n[1/2] Analisando ataques Brute Force...")
    bf_data = carregar_relatorios("bruteforce")
    if bf_data["vuln"] or bf_data["secure"]:
        comp_bf = comparar_bruteforce(bf_data["vuln"], bf_data["secure"])
        salvar_comparativo(comp_bf, "comparativo_bruteforce")
        print(f"\n  Conclusão: {comp_bf['conclusao']}")
    else:
        print("  ⚠ Nenhum relatório de brute force encontrado.")

    # DoS
    print(f"\n[2/2] Analisando ataques DoS...")
    dos_data = carregar_relatorios("dos")
    if dos_data["vuln"] or dos_data["secure"]:
        comp_dos = comparar_dos(dos_data["vuln"], dos_data["secure"])
        salvar_comparativo(comp_dos, "comparativo_dos")
        print(f"\n  Conclusão: {comp_dos['conclusao']}")
    else:
        print("  ⚠ Nenhum relatório de DoS encontrado.")

    print(f"\n{'='*60}")
    print("  Análise concluída!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
