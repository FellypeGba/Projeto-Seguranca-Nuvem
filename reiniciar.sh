#!/bin/bash
# Script de reinicialização limpa do ambiente SecCloud
set -e

echo "=== [1/4] Parando e removendo containers + imagens antigas ==="
docker compose down --rmi local --volumes 2>/dev/null || docker compose down 2>/dev/null || true

echo ""
echo "=== [2/4] Reconstruindo todas as imagens do zero ==="
docker compose build --no-cache

echo ""
echo "=== [3/4] Subindo todos os serviços ==="
docker compose up -d

echo ""
echo "=== [4/4] Aguardando APIs iniciarem (pode levar até 60s) ==="
echo "    Acompanhe os logs em outro terminal: docker compose logs -f"
echo ""

# Aguarda até 90 segundos pelas APIs
TIMEOUT=90
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  RUNNING=$(docker compose ps --status running 2>/dev/null | grep -c "api-" || true)
  if [ "$RUNNING" -ge 2 ]; then
    echo "    APIs prontas após ${ELAPSED}s!"
    break
  fi
  echo "    Aguardando... (${ELAPSED}s / ${TIMEOUT}s) — containers api rodando: $RUNNING"
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done

echo ""
echo "=== Status final dos containers ==="
docker compose ps

echo ""
echo "=== Teste de conectividade ==="
docker compose exec dashboard python - << 'PYEOF'
import requests, os, sys

tests = [
    ("API Vulneravel", os.environ.get("VULN_URL", "http://api-vulneravel:5000")),
    ("API Protegida",  os.environ.get("SECURE_URL", "http://api-protegida:5000")),
]

all_ok = True
for name, url in tests:
    try:
        r = requests.get(f"{url}/health", timeout=5)
        data = r.json()
        print(f"  [OK] {name}: {url} -> HTTP {r.status_code} | modo={data.get('modo','?')}")
    except Exception as e:
        print(f"  [ERRO] {name}: {url}")
        print(f"         {e}")
        all_ok = False

if all_ok:
    print("\n  Tudo OK! Acesse: http://localhost:5050")
else:
    print("\n  Algumas APIs nao responderam. Verifique: docker compose logs api-vulneravel")
    sys.exit(1)
PYEOF