const express = require("express");
const { pool } = require("../db");
const { MAX_INT, MAX_PRECO, inteiroPositivo, inteiroNaoNegativo } = require("../validacao");

const router = express.Router();

function validarProduto(body) {
  const { nome, preco, quantidade } = body || {};
  if (typeof nome !== "string" || !nome.trim() || nome.length > 100) {
    return "nome é obrigatório (texto de até 100 caracteres)";
  }
  if (typeof preco !== "number" || !Number.isFinite(preco) || preco < 0 || preco > MAX_PRECO) {
    return `preco é obrigatório (número entre 0 e ${MAX_PRECO})`;
  }
  if (!inteiroNaoNegativo(quantidade)) {
    return `quantidade é obrigatória (inteiro entre 0 e ${MAX_INT})`;
  }
  return null;
}

function lerId(req, res) {
  const id = Number(req.params.id);
  if (!inteiroPositivo(id)) {
    res.status(400).json({ erro: "id inválido" });
    return null;
  }
  return id;
}

router.get("/", async (req, res) => {
  const { rows } = await pool.query("SELECT id, nome, preco, quantidade FROM produtos ORDER BY id");
  res.json(rows);
});

router.get("/:id", async (req, res) => {
  const id = lerId(req, res);
  if (id === null) return;
  const { rows } = await pool.query("SELECT id, nome, preco, quantidade FROM produtos WHERE id = $1", [id]);
  if (!rows.length) return res.status(404).json({ erro: "produto não encontrado" });
  res.json(rows[0]);
});

router.post("/", async (req, res) => {
  const erro = validarProduto(req.body);
  if (erro) return res.status(400).json({ erro });
  const { nome, preco, quantidade } = req.body;
  const { rows } = await pool.query(
    "INSERT INTO produtos (nome, preco, quantidade) VALUES ($1, $2, $3) RETURNING id, nome, preco, quantidade",
    [nome.trim(), preco, quantidade]
  );
  res.status(201).json(rows[0]);
});

router.put("/:id", async (req, res) => {
  const id = lerId(req, res);
  if (id === null) return;
  const erro = validarProduto(req.body);
  if (erro) return res.status(400).json({ erro });
  const { nome, preco, quantidade } = req.body;
  const { rows } = await pool.query(
    "UPDATE produtos SET nome = $1, preco = $2, quantidade = $3 WHERE id = $4 RETURNING id, nome, preco, quantidade",
    [nome.trim(), preco, quantidade, id]
  );
  if (!rows.length) return res.status(404).json({ erro: "produto não encontrado" });
  res.json(rows[0]);
});

router.delete("/:id", async (req, res) => {
  const id = lerId(req, res);
  if (id === null) return;
  const { rowCount } = await pool.query("DELETE FROM produtos WHERE id = $1", [id]);
  if (!rowCount) return res.status(404).json({ erro: "produto não encontrado" });
  res.status(204).end();
});

module.exports = router;
