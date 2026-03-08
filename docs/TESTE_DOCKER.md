# Teste Docker - Simulação de Ataque em Nuvem

## Pré-requisitos

- Docker Desktop instalado e rodando (baixe em docker.com se necessário).

## Executando o Teste

### 1. Construir e iniciar os containers
```bash
docker-compose up --build
```

Isso irá:
- Construir as imagens da API e do Attacker.
- Iniciar a API na porta 5000.
- Executar o ataque automaticamente (5 requisições GET /admin).
- Gravar logs em `logs/api.log`.

Aguarde até ver as saídas dos containers (Attacker mostrará "403" 5 vezes).

## Verificar Logs e Métricas

Após o teste completar (Attacker para automaticamente):
```bash
python monitoramento/metricas.py
```

Você verá algo como:
```
Eventos registrados (linhas totais): 15
Acessos ao /admin: 5
```

## Parar o Teste

```bash
docker-compose down
```

Isso para e remove os containers.

## Observações

- Os logs ficam em `logs/api.log` (persistidos localmente via volume).
- Para limpar imagens: `docker-compose down --rmi all`.
- Se precisar alterar o ataque, edite `atacante/ataque_simples.py` e reconstrua.