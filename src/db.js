const { Pool, types } = require("pg");

// NUMERIC vem do Postgres como string; converte para número no JSON
types.setTypeParser(1700, (valor) => parseFloat(valor));

const host = process.env.DB_HOST;

// RDS PostgreSQL (versão 15+) exige SSL por padrão. Liga SSL automaticamente
// quando o host é do RDS, a não ser que DB_SSL=false seja informado.
const sslPadrao = host && host.includes("rds.amazonaws.com") ? "true" : "false";
const usarSsl = (process.env.DB_SSL || sslPadrao) === "true";

const pool = new Pool({
  host,
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME || "crud",
  user: process.env.DB_USER,
  password: process.env.DB_PASS,
  ssl: usarSsl ? { rejectUnauthorized: false } : false,
});

// Mesmas tabelas do app Flask original (idempotente: pode rodar com o banco já existente)
async function criarTabelas() {
  await pool.query(`CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    preco NUMERIC(10,2) NOT NULL)`);
  await pool.query("ALTER TABLE produtos ADD COLUMN IF NOT EXISTS quantidade INTEGER NOT NULL DEFAULT 0");
  await pool.query(`CREATE TABLE IF NOT EXISTS vendas (
    id SERIAL PRIMARY KEY,
    data TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valor_total NUMERIC(10,2) NOT NULL DEFAULT 0)`);
  await pool.query(`CREATE TABLE IF NOT EXISTS itens_venda (
    id SERIAL PRIMARY KEY,
    venda_id INTEGER NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
    produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL,
    produto_nome VARCHAR(100) NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario NUMERIC(10,2) NOT NULL)`);
}

module.exports = { pool, criarTabelas };
