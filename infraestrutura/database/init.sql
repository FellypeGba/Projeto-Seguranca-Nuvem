CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    public BOOLEAN DEFAULT TRUE
);

INSERT INTO users (name, public) VALUES
('Alice', TRUE),
('Bartolomeu', FALSE),
('Catarina', TRUE);