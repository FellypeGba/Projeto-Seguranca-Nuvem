# Teste Local - Simulação de Ataque em Nuvem

## Setup Inicial (rodar uma única vez)

### 1. Criar ambiente virtual
```bash
python -m venv venv
```

### 2. Ativar o ambiente virtual
No PowerShell:
```bash
venv\Scripts\activate
```

Você deve ver `(venv)` no início da linha do terminal.

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

## Executando o Teste

### Terminal 1 - API (Servidor Interno)
```bash
# Certifique-se de que o venv está ativado
# Edite infraestrutura/api/app.py e mude port=5000 para port=5001
python infraestrutura/api/app.py
```

Você verá:
```
 * Running on http://0.0.0.0:5001
```

**Deixe este terminal rodando.**

### Terminal 2 - Gateway (Ponto de Entrada)
Abra um novo PowerShell na pasta do projeto:
```bash
venv\Scripts\activate
# Edite infraestrutura/gateway/gateway.py e mude API_BASE_URL = "http://localhost:5001"
python infraestrutura/gateway/gateway.py
```

Você verá:
```
 * Running on http://0.0.0.0:5000
```

**Deixe este terminal rodando.**

### Terminal 3 - Ataque
Abra um terceiro PowerShell na pasta do projeto:
```bash
venv\Scripts\activate
# Certifique-se de que ataque_simples.py usa url = "http://localhost:5000/admin"
python atacante/ataque_simples.py
```

Você deve ver:
```
403
403
403
403
403
```

(5 requisições que falharam com status 403 - acesso proibido ao endpoint `/admin` via Gateway).

## Verificar Logs e Métricas

### Terminal 4 - Métricas
Abra um quarto PowerShell:
```bash
venv\Scripts\activate
python monitoramento/metricas.py
```

Você verá algo como:
```
=== MÉTRICAS DE MONITORAMENTO ===

GATEWAY (Ponto de Entrada):
  Total de requisições recebidas: 5
  Requisições para /data: 0
  Requisições para /admin: 5
  Requisições bem-sucedidas (200): 0
  Requisições bloqueadas (403): 5

API (Processamento Interno):
  Total de acessos processados: 5
  Acessos ao /data: 0
  Acessos ao /admin: 5
```

## Parar o Teste

1. Nos Terminais 1 e 2: pressione `Ctrl+C` para parar os servidores.
2. Nos outros: você pode fechar os terminais normalmente.

## Observações

- O Gateway age como proxy reverso, registrando requisições externas em `logs/gateway.log`.
- A API registra processamento interno em `logs/api.log`.
- Para teste local, ajuste as portas se houver conflitos (API na 5001, Gateway na 5000).
- O script simples faz apenas 5 requisições.