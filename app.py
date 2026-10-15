import os
from flask import Flask, request, redirect, render_template_string
import psycopg2

app = Flask(__name__)

def conectar():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ.get("DB_NAME", "crud"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
    )

def criar_tabela():
    with conectar() as con, con.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            preco NUMERIC(10,2) NOT NULL)""")

PAGINA = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cadastro de Produtos</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Segoe UI", Arial, sans-serif; background: #f1f4f9; color: #1e293b; }
  header { background: #232f3e; color: #fff; padding: 22px 16px; text-align: center; }
  header h1 { margin: 0; font-size: 26px; }
  header p { margin: 6px 0 0; color: #ff9900; font-size: 14px; }
  main { max-width: 760px; margin: 28px auto; padding: 0 16px; }
  .card { background: #fff; border-radius: 12px; padding: 22px; box-shadow: 0 2px 10px rgba(0,0,0,.08); margin-bottom: 22px; }
  .card h2 { margin: 0 0 14px; font-size: 18px; }
  form.cadastro { display: flex; gap: 10px; flex-wrap: wrap; }
  input { flex: 1; min-width: 150px; padding: 11px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 15px; }
  input:focus { outline: none; border-color: #ff9900; box-shadow: 0 0 0 3px rgba(255,153,0,.2); }
  button, .btn { padding: 11px 18px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-block; }
  .primario { background: #ff9900; color: #232f3e; }
  .primario:hover { background: #ec8b00; }
  .editar { background: #e0ecff; color: #1d4ed8; padding: 7px 12px; }
  .excluir { background: #fee2e2; color: #b91c1c; padding: 7px 12px; }
  .cancelar { background: #e2e8f0; color: #334155; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 13px; text-transform: uppercase; color: #64748b; padding: 10px; border-bottom: 2px solid #e2e8f0; }
  td { padding: 12px 10px; border-bottom: 1px solid #f1f5f9; }
  tr:hover td { background: #f8fafc; }
  .acoes { display: flex; gap: 6px; }
  .acoes form { margin: 0; }
  .vazio { text-align: center; color: #94a3b8; padding: 24px; }
  footer { text-align: center; color: #94a3b8; font-size: 13px; padding-bottom: 24px; }
</style>
</head>
<body>
<header>
  <h1>Cadastro de Produtos</h1>
  <p>Aplicação Flask · AWS EC2 + RDS PostgreSQL</p>
</header>
<main>
  <div class="card">
    <h2>{% if item %}Editar produto #{{ item[0] }}{% else %}Novo produto{% endif %}</h2>
    <form class="cadastro" method="post" action="{% if item %}/editar/{{ item[0] }}{% else %}/criar{% endif %}">
      <input name="nome" placeholder="Nome do produto" value="{{ item[1] if item else '' }}" required>
      <input name="preco" type="number" step="0.01" min="0" placeholder="Preço (R$)" value="{{ item[2] if item else '' }}" required>
      <button class="primario">{% if item %}Salvar{% else %}Adicionar{% endif %}</button>
      {% if item %}<a class="btn cancelar" href="/">Cancelar</a>{% endif %}
    </form>
  </div>
  <div class="card">
    <h2>Produtos cadastrados ({{ produtos|length }})</h2>
    <table>
      <tr><th>ID</th><th>Nome</th><th>Preço</th><th>Ações</th></tr>
      {% for p in produtos %}
      <tr>
        <td>{{ p[0] }}</td>
        <td>{{ p[1] }}</td>
        <td>R$ {{ "%.2f"|format(p[2])|replace(".", ",") }}</td>
        <td class="acoes">
          <a class="btn editar" href="/?editar={{ p[0] }}">Editar</a>
          <form method="post" action="/excluir/{{ p[0] }}" onsubmit="return confirm('Excluir este produto?')">
            <button class="excluir">Excluir</button>
          </form>
        </td>
      </tr>
      {% else %}
      <tr><td colspan="4" class="vazio">Nenhum produto cadastrado ainda.</td></tr>
      {% endfor %}
    </table>
  </div>
</main>
<footer>Trabalho 1 · Infraestrutura Cloud AWS · UNESC</footer>
</body>
</html>
"""

@app.route("/")
def listar():
    with conectar() as con, con.cursor() as cur:
        cur.execute("SELECT id, nome, preco FROM produtos ORDER BY id")
        produtos = cur.fetchall()
        item = None
        if request.args.get("editar"):
            cur.execute("SELECT id, nome, preco FROM produtos WHERE id=%s", (request.args["editar"],))
            item = cur.fetchone()
    return render_template_string(PAGINA, produtos=produtos, item=item)

@app.route("/criar", methods=["POST"])
def criar():
    with conectar() as con, con.cursor() as cur:
        cur.execute("INSERT INTO produtos (nome, preco) VALUES (%s, %s)",
                    (request.form["nome"], request.form["preco"]))
    return redirect("/")

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    with conectar() as con, con.cursor() as cur:
        cur.execute("UPDATE produtos SET nome=%s, preco=%s WHERE id=%s",
                    (request.form["nome"], request.form["preco"], id))
    return redirect("/")

@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    with conectar() as con, con.cursor() as cur:
        cur.execute("DELETE FROM produtos WHERE id=%s", (id,))
    return redirect("/")

criar_tabela()