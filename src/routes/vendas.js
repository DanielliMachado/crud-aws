const express = require("express");
const { pool } = require("../db");

const router = express.Router();

const SELECT_VENDAS = `
  SELECT v.id,
         v.data,
         to_char(v.data AT TIME ZONE 'America/Sao_Paulo', 'DD/MM/YYYY HH24:MI') AS data_formatada,
         v.valor_total,
         json_agg(json_build_object(
           'produto_id', i.produto_id,
           'produto_nome', i.produto_nome,
           'quantidade', i.quantidade,
           'preco_unitario', i.preco_unitario
         ) ORDER BY i.id) AS itens
  FROM vendas v
  JOIN itens_venda i ON i.venda_id = v.id`;

router.get("/", async (req, res) => {
  const { rows } = await pool.query(`${SELECT_VENDAS} GROUP BY v.id ORDER BY v.id DESC`);
  res.json(rows);
});

router.get("/resumo", async (req, res) => {
  const { rows } = await pool.query(
    "SELECT COUNT(*)::int AS quantidade_vendas, COALESCE(SUM(valor_total), 0) AS total_vendido FROM vendas"
  );
  res.json(rows[0]);
});

router.get("/:id", async (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id <= 0) return res.status(400).json({ erro: "id inválido" });
  const { rows } = await pool.query(`${SELECT_VENDAS} WHERE v.id = $1 GROUP BY v.id`, [id]);
  if (!rows.length) return res.status(404).json({ erro: "venda não encontrada" });
  res.json(rows[0]);
});

// Registra a venda e baixa o estoque numa única transação:
// se qualquer produto não tiver estoque suficiente, nada é gravado.
router.post("/", async (req, res) => {
  const itens = req.body && req.body.itens;
  if (!Array.isArray(itens)) {
    return res.status(400).json({ erro: "envie { itens: [{ produto_id, quantidade }] }" });
  }
  const validos = itens.filter((i) => i && Number.isInteger(i.quantidade) && i.quantidade > 0);
  if (!validos.length) {
    return res.status(400).json({ erro: "informe a quantidade de pelo menos um produto" });
  }
  if (validos.some((i) => !Number.isInteger(i.produto_id) || i.produto_id <= 0)) {
    return res.status(400).json({ erro: "produto_id inválido" });
  }

  const cliente = await pool.connect();
  try {
    await cliente.query("BEGIN");
    const venda = await cliente.query("INSERT INTO vendas DEFAULT VALUES RETURNING id");
    const vendaId = venda.rows[0].id;
    let total = 0;
    for (const { produto_id, quantidade } of validos) {
      const atualizado = await cliente.query(
        `UPDATE produtos SET quantidade = quantidade - $1
         WHERE id = $2 AND quantidade >= $1
         RETURNING nome, preco`,
        [quantidade, produto_id]
      );
      if (!atualizado.rows.length) {
        await cliente.query("ROLLBACK");
        return res.status(409).json({
          erro: "estoque insuficiente ou produto inexistente. Nada foi vendido.",
          produto_id,
        });
      }
      const { nome, preco } = atualizado.rows[0];
      await cliente.query(
        `INSERT INTO itens_venda (venda_id, produto_id, produto_nome, quantidade, preco_unitario)
         VALUES ($1, $2, $3, $4, $5)`,
        [vendaId, produto_id, nome, quantidade, preco]
      );
      total += preco * quantidade;
    }
    await cliente.query("UPDATE vendas SET valor_total = $1 WHERE id = $2", [total.toFixed(2), vendaId]);
    await cliente.query("COMMIT");

    const { rows } = await cliente.query(`${SELECT_VENDAS} WHERE v.id = $1 GROUP BY v.id`, [vendaId]);
    res.status(201).json(rows[0]);
  } catch (erro) {
    await cliente.query("ROLLBACK").catch(() => {});
    throw erro;
  } finally {
    cliente.release();
  }
});

module.exports = router;
