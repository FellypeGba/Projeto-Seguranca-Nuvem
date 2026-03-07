# API Contract – Cloud Security Simulation Lab

Este documento define os padrões atuais de comunicação entre os componentes do sistema:

- API da infraestrutura
- Aplicação atacante
- Sistema de monitoramento

Esses padrões podem evoluir conforme o projeto avança.

---

# 1. Arquitetura Atual

Fluxo básico da simulação:

```
Atacante → API → Logs → Monitoramento
```

Componentes:

| Componente | Função |
|------------|--------|
| atacante | executa ataques simulados |
| api | serviço principal da cloud simulada |
| monitoramento | coleta e analisa métricas |
| logs | armazenamento de eventos |

---

# 2. Endereço dos Serviços

Dentro do Docker Compose:

| Serviço | Endereço |
|--------|--------|
| API | http://api:5000 |
| Logs | /logs |

Para acesso externo:

| Serviço | Endereço |
|--------|--------|
| API | http://localhost:5000 |

---

# 3. Endpoints da API

## GET /data

Retorna dados públicos.

Exemplo de resposta:

```json
{
  "status": "success",
  "data": "public data"
}
```

---

## GET /admin

Endpoint administrativo (usado para simular tentativas de acesso indevido).

Resposta esperada sem autorização:

```json
{
  "status": "forbidden",
  "message": "admin access required"
}
```

HTTP Status:

```
403 Forbidden
```

---

# 4. Formato Padrão de Resposta da API

Todas as respostas devem seguir o formato:

```json
{
  "status": "success | error",
  "data": {},
  "message": ""
}
```

Campos:

| Campo | Descrição |
|------|------|
| status | indica sucesso ou erro |
| data | conteúdo retornado |
| message | mensagem opcional |

---

# 5. Registro de Logs

Eventos relevantes devem ser registrados em:

```
/logs/api.log
```

Formato padrão do log (JSON):

```json
{
  "timestamp": "2026-03-07T18:00:00",
  "source": "attacker",
  "endpoint": "/admin",
  "method": "GET",
  "status_code": 403,
  "attack_type": "unauthorized_access"
}
```

Campos:

| Campo | Descrição |
|------|------|
| timestamp | momento do evento |
| source | origem da requisição |
| endpoint | endpoint acessado |
| method | método HTTP |
| status_code | código de resposta |
| attack_type | tipo de ataque detectado |

---

# 6. Aplicação Atacante

A aplicação atacante deve enviar requisições HTTP para a API.

Exemplo de ataque inicial:

```
GET /admin
```

Objetivo:

Simular tentativa de acesso não autorizado.

---

# 7. Monitoramento

O sistema de monitoramento deve ler os arquivos de log e extrair métricas como:

- número de ataques realizados
- número de ataques bem sucedidos
- número de ataques bloqueados

---

# 8. Estrutura de Diretórios

```
.
├── docker-compose.yml
├── atacante/
├── infraestrutura/
│   ├── api/
│   ├── interno/
│   └── database/
├── monitoramento/
├── logs/
└── docs/
```

---