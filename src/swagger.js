const erro = {
  type: "object",
  properties: { erro: { type: "string" } },
};

const respostaErro = (descricao) => ({
  description: descricao,
  content: { "application/json": { schema: { $ref: "#/components/schemas/Erro" } } },
});

const parametroId = {
  name: "id",
  in: "path",
  required: true,
  schema: { type: "integer", minimum: 1, maximum: 2147483647 },
};

const json = (schema) => ({ "application/json": { schema } });

module.exports = {
  openapi: "3.0.3",
  info: {
    title: "CRUD AWS - Produtos",
    version: "2.0.0",
    description:
      "API REST de produtos (Node.js + Express + PostgreSQL). " +
      "Deploy na AWS: EC2 + RDS PostgreSQL + Nginx. Trabalho de Infraestrutura Cloud, UNESC. " +
      "Nenhum endpoint exige autenticação.",
  },
  servers: [{ url: "/" }],
  tags: [{ name: "Produtos" }, { name: "Sistema" }],
  paths: {
    "/health": {
      get: {
        tags: ["Sistema"],
        summary: "Verifica se a API e o banco estão no ar",
        responses: {
          200: { description: "OK", content: json({ type: "object", properties: { status: { type: "string" }, banco: { type: "string" } } }) },
          503: respostaErro("Banco de dados indisponível"),
        },
      },
    },
    "/produtos": {
      get: {
        tags: ["Produtos"],
        summary: "Lista todos os produtos",
        responses: {
          200: { description: "Lista de produtos", content: json({ type: "array", items: { $ref: "#/components/schemas/Produto" } }) },
        },
      },
      post: {
        tags: ["Produtos"],
        summary: "Cadastra um produto",
        requestBody: { required: true, content: json({ $ref: "#/components/schemas/ProdutoEntrada" }) },
        responses: {
          201: { description: "Produto criado", content: json({ $ref: "#/components/schemas/Produto" }) },
          400: respostaErro("Dados inválidos"),
        },
      },
    },
    "/produtos/{id}": {
      parameters: [parametroId],
      get: {
        tags: ["Produtos"],
        summary: "Busca um produto pelo id",
        responses: {
          200: { description: "Produto", content: json({ $ref: "#/components/schemas/Produto" }) },
          404: respostaErro("Produto não encontrado"),
        },
      },
      put: {
        tags: ["Produtos"],
        summary: "Atualiza um produto",
        requestBody: { required: true, content: json({ $ref: "#/components/schemas/ProdutoEntrada" }) },
        responses: {
          200: { description: "Produto atualizado", content: json({ $ref: "#/components/schemas/Produto" }) },
          400: respostaErro("Dados inválidos"),
          404: respostaErro("Produto não encontrado"),
        },
      },
      delete: {
        tags: ["Produtos"],
        summary: "Exclui um produto",
        responses: {
          204: { description: "Produto excluído" },
          404: respostaErro("Produto não encontrado"),
        },
      },
    },
  },
  components: {
    schemas: {
      Erro: erro,
      ProdutoEntrada: {
        type: "object",
        required: ["nome", "preco", "quantidade"],
        properties: {
          nome: { type: "string", maxLength: 100, example: "Teclado" },
          preco: { type: "number", minimum: 0, maximum: 99999999.99, example: 129.9 },
          quantidade: { type: "integer", minimum: 0, maximum: 2147483647, example: 10 },
        },
      },
      Produto: {
        type: "object",
        properties: {
          id: { type: "integer", example: 1 },
          nome: { type: "string", example: "Teclado" },
          preco: { type: "number", example: 129.9 },
          quantidade: { type: "integer", example: 10 },
        },
      },
    },
  },
};
