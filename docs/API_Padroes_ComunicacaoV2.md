# API Contract – Cloud Security Simulation Lab v2

Este documento define os padrões de comunicação da versão atual do sistema, com Gateway como ponto de entrada.

---

## Arquitetura Atual

```
Atacante → Gateway → API → Logs → Monitoramento
```

| Componente | Função |
|------------|--------|
| atacante | executa ataques simulados |
| gateway | proxy reverso e ponto de entrada |
| api | serviço principal da cloud simulada |
| monitoramento | coleta e analisa métricas |
| logs | armazenamento de eventos |

---

## Endereços dos Serviços

**Docker Compose:**
- Gateway: `http://gateway:5000`
- API: `http://api:5000` (interno)

**Acesso Externo:**
- Gateway: `http://localhost:5000`

---

## Endpoints

### GET /data
Retorna dados públicos (200 OK).

### GET /admin
Endpoint administrativo - sempre retorna 403 Forbidden.

**Resposta padrão:**
```json
{"status": "success|error|forbidden", "data": {}, "message": ""}
```

---

## Logs

- **Gateway:** `/logs/gateway.log` (Docker) ou `./logs/gateway.log` (local)
- **API:** `/logs/api.log` (Docker) ou `./logs/api.log` (local)

**Formato:** Timestamp + INFO + detalhes da requisição/resposta.

---

## Monitoramento

Lê logs do Gateway e API, gera métricas:
- Total de requisições/acessos
- Por endpoint (/data, /admin)
- Status (200/403)
- Consistência entre componentes

---

## Estrutura de Diretórios

```
.
├── docker-compose.yml
├── atacante/
├── docs/
├── infraestrutura/
│   ├── api/
│   ├── database/
│   ├── gateway/
│   └── interno/
├── logs/
└── monitoramento/
```