# Projeto Final de Segurança Computacional: Simulação de Ataques a um Ambiente de Nuvem

## 📌 Descrição

Este projeto tem como objetivo simular uma situação de ataque maliciosos a um ambiente de nuvem. Para isso, será utilizado a tecnologia de docker para criar um container semelhante a uma pequena cloud, com base de dados, serviços internos e uma api de acesso. Então uma aplicação em Python realizará ataques a nuvem, que pode estar num modo mais protegido ou não. Enquanto isso, outro sistema, responsável por registrar tudo em um log usará de métricas para ser possível comparar as consequências do ataque nos dois estados da api da nuvem.

## 🏗️ Estrutura Base
```text
projeto-seguranca-nuvem/
├── docker-compose.yml
├── requirements.txt
├── atacante/
├── docs/
├── infraestrutura/
│   ├── api/
│   ├── interno/
│   └── database/
├── logs/
└── monitoramento/
```

### ✅ atacante
Aplicação responsável por se passar por um atacante, utilizando diversas estratégias para tentar invadir o serviço de nuvem

### ✅ docs
Aqui fica descrições estruturais e a arquitetura do projeto

### ✅ infraestutura
Onde reside a aplicação de nuvem, com a api de acesso, a pasta interno onde supostamente deveria ser protegido e o banco de dados (database)

### ✅ logs
Onde ser armazenam os resultados de logs criando na execução do sistema como um todo

### ✅ monitoramento
Parte que visa capturar os resultados dos ataques ao ambiente de nuvem e avaliar os danos causados de acordos com as métricas estabelicidas para escrever na seção de logs

## 💻 Como Rodar
Para rodar essa aplicação, acesse os dois documentos na pasta docs:

### TESTE_DOCKER
Mostrar como fazer um teste inicial usando o docker

### TESTE_LOCAL
Indica como fazer um teste local, sem uso do docker  

**Observação:** Importante se atentar na url que o ataque irá buscar, pois se muda se for docker ou local