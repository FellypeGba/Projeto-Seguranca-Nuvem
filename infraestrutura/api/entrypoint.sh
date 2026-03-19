#!/bin/bash
set -e

echo "=== Executando seed (migration + dados) ==="
python seed.py

echo "=== Iniciando API Flask ==="
python app.py
