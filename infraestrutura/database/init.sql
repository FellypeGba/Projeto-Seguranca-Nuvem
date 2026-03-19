-- Tabela de usuários para autenticação (Brute Force)
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- Tabela de registros pesados para relatório (DoS)
CREATE TABLE IF NOT EXISTS registros_relatorio (
    id SERIAL PRIMARY KEY,
    data_transacao TIMESTAMP NOT NULL,
    valor NUMERIC(12, 2) NOT NULL,
    descricao TEXT NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL
);