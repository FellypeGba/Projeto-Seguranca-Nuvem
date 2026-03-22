# Arquitetura Inicial – Cloud Security Lab

Este documento descreve a arquitetura básica do ambiente de nuvem simulado utilizado no projeto.

O objetivo é reproduzir, de forma simplificada, uma arquitetura comum em ambientes cloud para permitir a simulação de ataques e coleta de métricas de segurança.

---

# Visão Geral da Arquitetura

Fluxo principal de comunicação:

```
Atacante → Gateway → API → Database
                     ↓
               Serviço Interno
```

Componentes:

| Componente | Função |
|------------|--------|
| Atacante | Simula requisições e ataques ao sistema |
| Gateway | Ponto de entrada da aplicação |
| API | Serviço principal da aplicação |
| Serviço Interno | Serviço acessível apenas pela API |
| Database | Armazenamento de dados |
| Monitoramento | Coleta e análise de logs |

---

# Estrutura de Serviços

Arquitetura simplificada:

```
                +-----------+
                | Atacante  |
                +-----------+
                      |
                      v
                +-----------+
                |  Gateway  |
                +-----------+
                      |
                      v
                +-----------+
                |    API    |
                +-----------+
                  |       |
                  v       v
        +---------------+  +-----------+
        | Serviço Interno | | Database |
        +---------------+  +-----------+
```

Todos os componentes são executados em containers Docker e conectados por uma rede interna.

---

# Ordem de Implementação

Para permitir desenvolvimento paralelo, os componentes devem ser implementados na seguinte ordem:

### 1. Gateway

Responsável por receber todas as requisições externas.

Funções:
- ponto de entrada do sistema
- encaminhamento de requisições para a API
- registro inicial de logs

Fluxo:

```
Atacante → Gateway → API
```

---

### 2. Serviço Interno

Serviço acessível apenas pela API.

Objetivo:
- simular microserviços internos de um ambiente cloud
- permitir testes de acesso indevido à rede interna

Fluxo:

```
API → Serviço Interno
```

---

### 3. Database

Responsável por armazenar dados da aplicação.

Objetivo:
- simular persistência de dados
- permitir experimentos com acesso a dados

Fluxo:

```
API → Database
```

---

### 4. Autenticação

Sistema simples de autenticação baseado em token.

Objetivo:
- simular controle de acesso
- permitir ataques como:
  - brute force
  - acesso não autorizado
  - privilege escalation

Exemplo de fluxo:

```
POST /login → retorna token
GET /admin → requer token
```

---

# Objetivo da Arquitetura

Essa estrutura permite simular cenários comuns de segurança em nuvem, como:

- acesso direto a serviços internos
- bypass de gateway
- tentativas de acesso administrativo
- ataques de autenticação
- análise de logs e métricas de ataque