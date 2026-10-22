require("dotenv").config();

const express = require("express");
const swaggerUi = require("swagger-ui-express");
const { pool, criarTabelas } = require("./db");
const swaggerSpec = require("./swagger");
const produtos = require("./routes/produtos");
const vendas = require("./routes/vendas");

const app = express();
app.use(express.json());

app.get("/", (req, res) => res.redirect("/docs"));
app.use("/docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));
app.get("/openapi.json", (req, res) => res.json(swaggerSpec));

app.get("/health", async (req, res) => {
  try {
    await pool.query("SELECT 1");
    res.json({ status: "ok", banco: "ok" });
  } catch (erro) {
    res.status(503).json({ erro: "banco de dados indisponível" });
  }
});

app.use("/produtos", produtos);
app.use("/vendas", vendas);

app.use((req, res) => res.status(404).json({ erro: "rota não encontrada" }));

// Express 5 encaminha para cá os erros lançados nas rotas async
app.use((erro, req, res, next) => {
  if (erro.type === "entity.parse.failed") {
    return res.status(400).json({ erro: "JSON inválido no corpo da requisição" });
  }
  console.error(erro);
  res.status(500).json({ erro: "erro interno no servidor" });
});

const PORT = Number(process.env.PORT || 3000);

criarTabelas()
  .then(() => {
    app.listen(PORT, () => console.log(`API rodando na porta ${PORT} — Swagger em /docs`));
  })
  .catch((erro) => {
    console.error("Não foi possível conectar ao banco / criar tabelas:", erro.message || erro.code || erro);
    process.exit(1);
  });
