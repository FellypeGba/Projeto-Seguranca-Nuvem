# Arquitetura Atual – Cloud Security Lab v2

Este documento descreve a arquitetura atual e implementada do ambiente de nuvem simulado utilizado no projeto.

A evolução da primeira versão consolida os componentes, introduce o dashboard como orquestrador visual e implementa um modelo comparativo com duas versões da API (vulnerável e protegida).

---

## 🎯 Objetivo

Simular um ambiente de nuvem com dois modos operacionais para:
- **Modo Vulnerável**: Sem proteção adicional - permite visualizar ataques bem-sucedidos
- **Modo Protegido**: Com mecanismos de segurança ativados - permite comparar efetividade das proteções
- **Análise Comparativa**: Via logs e métricas, avaliar o impacto dos ataques em ambos os cenários

---

## 🏗️ Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                       DASHBOARD (Flask)                          │
│                 Interface Web - localhost:5050                   │
│              Orquestração, Status e Análise de Logs              │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
        ┌───────▼────────┐         ┌───────▼────────┐
        │  API Vulnerável │        │ API Protegida  │
        │   (FastAPI)     │        │   (FastAPI)    │
        │  :8081 / :5000  │        │  :8082 / :5000 │
        │ MODO_PROTEGIDO  │        │ MODO_PROTEGIDO │
        │      = False    │        │      = True    │
        └────────┬────────┘        └────────┬────────┘
                 │                          │
                 └──────────────┬───────────┘
                                │
                     ┌──────────▼──────────┐
                     │   Database          │
                     │  PostgreSQL         │
                     │  :5432             │
                     └─────────────────────┘
                
        ┌─────────────────────────────────────────────┐
        │         Serviço Interno (Protegido)          │
        │          Acessível apenas pela API           │
        │              (não está em rede)              │
        └─────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│    ATACANTE (Python + Wordlist)             │
│   Simula requisições maliciosas             │
│     (Externo à rede Docker)                 │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│         MONITORAMENTO (Metrics)             │
│    Coleta análise de logs e resultados     │
│      (Processa entrada/saída de logs)      │
└────────────────────────────────────────────┘
```

---

## 📦 Componentes Principais

### 1. **Dashboard (Flask)**
**Porta**: 5050  
**Tecnologia**: Flask + Web Interface  
**Responsabilidades**:
- Ponto de acesso central (localhost:5050)
- Interface visual para gerenciar ataques
- Monitoramento em tempo real do status das APIs
- Visualização de logs de ambas as versões
- Execução de ataques através da interface
- Orquestração de wordlists e estratégias
- Comparação visual entre modo vulnerável e protegido

**Comunicação**:
```
Usuário → Dashboard → API Vulnerável (:8081)
                   → API Protegida (:8082)
                   → Leitura de Logs
```

---

### 2. **APIs (FastAPI x2)**

#### **API Vulnerável**
**Porta Externo**: 8081  
**Porta Container**: 5000  
**Modo**: `MODO_PROTEGIDO=False`

**Características**:
- Sem validações de segurança reforçada
- Sem rate limiting
- Autenticação básica (tokens simples)
- Sem proteção contra força bruta
- Acesso sem restrições

#### **API Protegida**
**Porta Externo**: 8082  
**Porta Container**: 5000  
**Modo**: `MODO_PROTEGIDO=True`

**Características**:
- Validações de segurança ativadas
- Rate limiting implementado
- Autenticação robusta
- Proteção contra força bruta
- Limites de recursos (CPU 0.5)
- Logs de segurança reforçados

**Endpoints Comuns**:
```
POST   /login           → Autenticação
GET    /relatorios      → Leitura de dados
POST   /relatorios      → Criação de dados
GET    /admin/info      → Info administrativa (restrita)
GET    /health          → Status da API
GET    /internal-call   → Acesso ao serviço interno
```

**Comunicação**:
```
API → Database (PostgreSQL)
   → Serviço Interno (requisições autorizadas)
   → Logging (/logs/api_vulneravel.log ou /logs/api_protegida.log)
```

---

### 3. **Database (PostgreSQL)**
**Porta**: 5432  
**Tecnologia**: PostgreSQL 15+  

**Responsabilidades**:
- Armazenamento de usuários
- Armazenamento de registros de relatório
- Auditoria de transações

**Tabelas**:
- `usuarios` - Credenciais e perfis
- `registros_relatorio` - Dados de transações

**Características**:
- Health check a cada 10s
- Seed automático na inicialização
- Backup de logs de transações

---

### 4. **Serviço Interno (Python)**
**Tecnologia**: Python (FastAPI/Flask)  
**Acesso**: Apenas via API (rede interna Docker)

**Responsabilidades**:
- Simular microserviços internos
- Processar requisições autorizadas da API
- Cenário de teste: acesso indevido à rede interna

**Segurança**:
- Não está exposto na rede externa
- Requer autenticação via API
- Logs de acesso isolados

---

### 5. **Atacante (Python)**
**Tecnologia**: Python + Wordlist  
**Componentes**:
- `atacar.py` - Script de ataque
- `wordlist.txt` - Dicionário de senhas
- `Dockerfile` - Containerização (opcional)

**Responsabilidades**:
- Simular tentativas de acesso malicioso
- Brute force de credenciais
- Testes de vulnerabilidades conhecidas
- Geração de logs de ataque

**Estratégias de Ataque**:
- Força bruta em `/login`
- SQL Injection em endpoints
- Privilege escalation
- Acesso direto ao serviço interno
- Bypass de autenticação

---

### 6. **Monitoramento (Metrics)**
**Tecnologia**: Python + File Watcher  

**Responsabilidades**:
- Coleta de logs das APIs
- Análise de padrões de ataque
- Cálculo de métricas de segurança
- Geração de relatórios comparativos

**Métricas Coletadas**:
- Taxa de requisições bem-sucedidas/falhadas
- Tentativas de acesso negado
- Tempo de resposta
- Tipos de ataque detectados
- Impacto comparativo (Vulnerável vs Protegido)

---

## 🔄 Fluxo de Comunicação

### Cenário 1: Ataque via Dashboard
```
1. Usuário inicia ataque no Dashboard (:5050)
2. Dashboard envia requisições para API Vulnerável (:8081)
3. API Vulnerável processa e registra em log
4. Dashboard envia mesmas requisições para API Protegida (:8082)
5. API Protegida processa com proteções
6. Monitoramento lê logs das duas APIs
7. Dashboard exibe resultado comparativo
```

### Cenário 2: Ataque Direto
```
1. Atacante executa atacar.py
2. Envia requisições para API Vulnerável (:8081)
3. Envia requisições para API Protegida (:8082)
4. APIs registram tentativas em logs
5. Monitoramento coleta dados
6. Dashboard visualiza resultados
```

### Cenário 3: Acesso ao Serviço Interno
```
1. Atacante tenta acessar Serviço Interno
2. API Vulnerável: Pode permitir sem validação
3. API Protegida: Bloqueia por falta de autorização
4. Logs registram tentativas
5. Monitoramento contabiliza diferenças
```

---

## 🐋 Orquestração Docker

### Serviços (docker-compose.yml)
```yaml
Services:
  - database       # PostgreSQL :5432
  - api-vulneravel # FastAPI :8081 → :5000
  - api-protegida  # FastAPI :8082 → :5000
  - dashboard      # Flask :5050
```

### Rede Interna
- **Driver**: Bridge (`seccloud`)
- **Todos os serviços**: Conectados na mesma rede
- **DNS Interno**: Resolução automática por nome de serviço

### Volumes
- `./logs` - Compartilhado entre todas as APIs e Dashboard
- `./atacante/wordlist.txt` - Compartilhado com Dashboard (read-only)

---

## 📊 Estrutura de Diretórios Implementada

```
projeto-seguranca-nuvem/
│
├── 📄 docker-compose.yml      # Orquestração de serviços
├── 📄 requirements.txt         # Dependências gerais
├── 📄 readme.md               # Instruções de execução
├── 📄 reiniciar.sh            # Script de restart completo
│
├── 📁 atacante/
│   ├── 📄 atacar.py           # Script de ataque
│   ├── 📄 Dockerfile          # Container do atacante
│   └── 📄 wordlist.txt        # Dicionário de senhas
│
├── 📁 dashboard/
│   ├── 📄 app.py              # Aplicação Flask
│   ├── 📄 Dockerfile          # Container do dashboard
│   ├── 📄 requirements.txt    # Dependências Flask
│   └── 📁 templates/
│       └── 📄 index.html      # Interface web
│
├── 📁 infraestrutura/
│   ├── 📁 api/
│   │   ├── 📄 app.py          # Aplicação FastAPI (2 instâncias)
│   │   ├── 📄 Dockerfile      # Container da API
│   │   ├── 📄 entrypoint.sh   # Script de inicialização
│   │   ├── 📄 requirements.txt # Dependências FastAPI
│   │   └── 📄 seed.py         # Dados iniciais (usuários)
│   │
│   ├── 📁 database/
│   │   ├── 📄 Dockerfile      # Container PostgreSQL
│   │   └── 📄 init.sql        # Schema inicial
│   │
│   └── 📁 interno/
│       └── 📄 servico.py      # Serviço interno (protegido)
│
├── 📁 monitoramento/
│   └── 📄 metricas.py         # Coleta e análise de métricas
│
├── 📁 logs/                   # Volume de logs (gerado em execução)
│   ├── api_vulneravel.log
│   ├── api_protegida.log
│   └── ... (outros logs)
│
└── 📁 docs/
    ├── 📄 Arquitetura_v1.md   # Versão anterior (referência)
    ├── 📄 Arquitetura_v2.md   # Esta versão (atual)
    ├── 📄 sequencia_de_acoes.txt
    └── 📁 VersoesAntigas/     # Documentação histórica
```

---

## 🔐 Comparativo: Vulnerável vs Protegido

| Aspecto | Vulnerável | Protegido |
|---------|-----------|-----------|
| **Validação** | Mínima | Rigorosa |
| **Rate Limiting** | Não | Sim |
| **Brute Force** | Permitido | Bloqueado |
| **Logs** | Básicos | Detalhados |
| **Timeout** | Padrão | Customizado |
| **Recursos** | Ilimitados | CPU Limitada (0.5) |
| **SQL Injection** | Vulnerável | Preparado |
| **CORS** | Aberto | Restritivo |
| **Token** | Simples | Verificado |

---

## 🚀 Ciclo de Execução

```
1. Inicialização
   ├─ docker-compose up
   ├─ PostgreSQL inicializa
   ├─ Seed.py carrega dados
   └─ APIs e Dashboard ficam prontos

2. Operação
   ├─ Dashboard monitora status das APIs
   ├─ Usuário inicia ataques via interface
   ├─ Atacante executa requisições maliciosas
   └─ Ambas as APIs processam em paralelo

3. Monitoramento
   ├─ Logs são escritos em tempo real
   ├─ Monitoramento coleta métricas
   ├─ Dashboard exibe resultados
   └─ Comparação visual entre modos

4. Encerramento
   └─ docker-compose down (limpa containers)
```

---

## 📝 Variáveis de Ambiente

**Database**:
```
POSTGRES_DB=mydb
POSTGRES_USER=user
POSTGRES_PASSWORD=password
```

**APIs**:
```
MODO_PROTEGIDO=False   # ou True
DATABASE_URL=postgresql://user:password@database:5432/mydb
```

**Dashboard**:
```
VULN_URL=http://api-vulneravel:5000
SECURE_URL=http://api-protegida:5000
WORDLIST_PATH=/wordlist.txt
LOG_DIR=/logs
```

---

## ✅ Status de Implementação

- ✅ Dashboard funcional com interface web
- ✅ Duas versões da API (vulnerável e protegida)
- ✅ Database com seed automático
- ✅ Monitoramento via ficheiros de log
- ✅ Docker Compose orquestrando tudo
- ✅ Atacante com wordlist
- ✅ Serviço Interno para testes
