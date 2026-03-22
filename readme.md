# Projeto Final de Segurança Computacional: Simulação de Ataques a um Ambiente de Nuvem

## 📌 Descrição

Este projeto tem como objetivo simular uma situação de ataque maliciosos a um ambiente de nuvem. Para isso, será utilizado a tecnologia de docker para criar um container semelhante a uma pequena cloud, com base de dados, serviço interno e uma api de acesso. Então uma aplicação em Python realizará ataques a nuvem, que pode estar num modo mais protegido ou não. Enquanto isso, outro módulo, responsável por registrar tudo em um log, usará de métricas para ser possível comparar as consequências do ataque nos dois estados da api da nuvem.

## 🏗️ Estrutura Base
```text
projeto-seguranca-nuvem/
├── docker-compose.yml
├── atacante/
├── dashborad/
├── docs/
├── infraestrutura/
│   ├── api/
│   ├── database/
│   └── interno/
├── logs/
└── monitoramento/
```

### ✅ atacante
Aplicação responsável por se passar por um atacante, utilizando diversas estratégias para tentar invadir o serviço de nuvem

### ✅ dashboard
Diretório com a interface que gerencia os ataques feitos ao sistema,
o estado das APIs, resultados dos ataques e os logs das aplicações.

### ✅ docs
Aqui fica descrições estruturais e a arquitetura do projeto

### ✅ infraestutura
Onde reside a aplicação de nuvem, com a api de acesso, a pasta  de serviço interno e o banco de dados (database)

### ✅ logs
Onde ser armazenam os resultados de logs criando na execução do sistema como um todo

### ✅ monitoramento
Parte que visa capturar os resultados dos ataques ao ambiente de nuvem e avaliar os danos causados de acordos com as métricas estabelicidas para escrever na seção de logs

## 💻 Como Rodar
Para uma análise completa do projeto, acesse na pasta o docs:
**Tutorial_SecCloud.docx**  
Para um teste das funcionalidades siga estes passos:

### 1. Pré-requisitos
Python mais recente instalado na Máquina;  
Docker Desktop em execução;  

### 2. Ativação dos Componentes
bash reiniciar.sh — faz rebuild completo e inicia todos os containers
```bash
bash reiniciar.sh
```
Aguarde o :8081 e o :8082 ficarem verdes no header do dashboard

### 3. Visualização da Interface de Ataque
Acesse: http://localhost:5050

### 4. Execução de comandos
Na pasta docs, acesse **Tutorial_SecCloud.docx** para todas as ações
possíveis no sistema

### 5. Sair do Sistema
Para encerrar aplicação, basta executar no terminal:
```bash
docker-compose down
```
