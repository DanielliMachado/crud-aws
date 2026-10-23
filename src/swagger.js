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
    title: "CRUD AWS - Produtos e Vendas",
    version: "2.0.0",
    description:
      "API REST de produtos e vendas (Node.js + Express + PostgreSQL). " +
      "Deploy na AWS: EC2 + RDS PostgreSQL + Nginx. Trabalho de Infraestrutura Cloud, UNESC. " +
      "Nenhum endpoint exige autenticação.",
  },
  servers: [{ url: "/" }],
  tags: [{ name: "Produtos" }, { name: "Vendas" }, { name: "Sistema" }],
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
        description: "Vendas antigas continuam registradas: o item da venda guarda o nome e o preço do produto.",
        responses: {
          204: { description: "Produto excluído" },
          404: respostaErro("Produto não encontrado"),
        },
      },
    },
    "/vendas": {
      get: {
        tags: ["Vendas"],
        summary: "Histórico de vendas (mais recentes primeiro)",
        responses: {
          200: { description: "Lista de vendas", content: json({ type: "array", items: { $ref: "#/components/schemas/Venda" } }) },
        },
      },
      post: {
        tags: ["Vendas"],
        summary: "Registra uma venda e baixa o estoque",
        description:
          "Tudo acontece numa única transação: se algum produto não tiver estoque suficiente, " +
          "nada é vendido e a API responde 409. Se algum item for inválido, a venda inteira é recusada com 400. " +
          "Itens com quantidade 0 são ignorados; o mesmo produto repetido tem as quantidades somadas.",
        requestBody: { required: true, content: json({ $ref: "#/components/schemas/VendaEntrada" }) },
        responses: {
          201: { description: "Venda registrada", content: json({ $ref: "#/components/schemas/Venda" }) },
          400: respostaErro("Item inválido ou nenhum item com quantidade"),
          409: respostaErro("Estoque insuficiente ou produto inexistente"),
        },
      },
    },
    "/vendas/resumo": {
      get: {
        tags: ["Vendas"],
        summary: "Quantidade de vendas e total vendido",
        responses: {
          200: {
            description: "Resumo",
            content: json({
              type: "object",
              properties: {
                quantidade_vendas: { type: "integer", example: 3 },
                total_vendido: { type: "number", example: 259.7 },
              },
            }),
          },
        },
      },
    },
    "/vendas/{id}": {
      parameters: [parametroId],
      get: {
        tags: ["Vendas"],
        summary: "Busca uma venda pelo id",
        responses: {
          200: { description: "Venda", content: json({ $ref: "#/components/schemas/Venda" }) },
          404: respostaErro("Venda não encontrada"),
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
      VendaEntrada: {
        type: "object",
        required: ["itens"],
        properties: {
          itens: {
            type: "array",
            items: {
              type: "object",
              required: ["produto_id", "quantidade"],
              properties: {
                produto_id: { type: "integer", minimum: 1, maximum: 2147483647, example: 1 },
                quantidade: { type: "integer", minimum: 0, maximum: 2147483647, example: 2 },
              },
            },
          },
        },
      },
      Venda: {
        type: "object",
        properties: {
          id: { type: "integer", example: 1 },
          data: { type: "string", format: "date-time" },
          data_formatada: { type: "string", example: "22/10/2026 14:30" },
          valor_total: { type: "number", example: 259.8 },
          itens: {
            type: "array",
            items: {
              type: "object",
              properties: {
                produto_id: { type: "integer", nullable: true, example: 1 },
                produto_nome: { type: "string", example: "Teclado" },
                quantidade: { type: "integer", example: 2 },
                preco_unitario: { type: "number", example: 129.9 },
              },
            },
          },
        },
      },
    },
  },
};
