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

### Terminal 1 - API (Servidor)
```bash
# Certifique-se de que o venv está ativado
python infraestrutura/api/app.py
```

Você verá:
```
 * Running on http://0.0.0.0:5000
```

**Deixe este terminal rodando.**

### Terminal 2 - Ataque
Abra um novo PowerShell na pasta do projeto:
```bash
venv\Scripts\activate
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

(5 requisições que falharam com status 403 - acesso proibido ao endpoint `/admin`).

## Verificar Logs e Métricas

### Terminal 3 - Métricas
Abra um terceiro PowerShell:
```bash
venv\Scripts\activate
python monitoramento/metricas.py
```

Você verá algo como:
```
Eventos registrados: 5
```

## Parar o Teste

1. No Terminal 1 (API): pressione `Ctrl+C` para parar o servidor.
2. Nos outros: você pode fechar os terminais normalmente.

## Observações

- Os logs da API ficam em `logs/api.log`
- Se a porta 5000 estiver ocupada, edite `infraestrutura/api/app.py` e mude a última linha para `app.run(host="0.0.0.0", port=5001)`, e ajuste a URL em `atacante/ataque_simples.py` para `http://localhost:5001/admin`.
- O script simples faz apenas 5 requisições. Para variar, edite `atacante/ataque_simples.py`.
