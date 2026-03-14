# Teste Docker - Simulação de Ataque em Nuvem

## Pré-requisitos

- Docker Desktop instalado e rodando (baixe em docker.com se necessário).

## Executando o Teste

### 1. Construir e iniciar os containers
```bash
docker-compose up --build
```

Isso irá:
- Construir as imagens do Gateway, API e Attacker.
- Iniciar o Gateway na porta 5000 (ponto de entrada).
- Iniciar a API internamente (porta 5000 na rede Docker).
- Executar o ataque automaticamente via Gateway (5 requisições GET /admin).
- Gravar logs em `logs/gateway.log` (gateway) e `logs/api.log` (API).

Aguarde até ver as saídas dos containers (Attacker mostrará "403" 5 vezes).

## Verificar Logs e Métricas

Após o teste completar (Attacker para automaticamente):
```bash
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

```bash
docker-compose down
```

Isso para e remove os containers.

## Observações

- O Gateway age como proxy reverso, registrando todas as requisições externas.
- Os logs ficam em `logs/gateway.log` e `logs/api.log` (persistidos localmente via volume).
- Para limpar imagens: `docker-compose down --rmi all`.