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
<!doctype html><html><head><meta charset="utf-8"><title>Produtos</title></head>
<body style="font-family:sans-serif;max-width:650px;margin:40px auto">
<h1>Cadastro de Produtos</h1>
<form method="post" action="{% if item %}/editar/{{ item[0] }}{% else %}/criar{% endif %}">
  <input name="nome" placeholder="Nome" value="{{ item[1] if item else '' }}" required>
  <input name="preco" type="number" step="0.01" placeholder="Preço" value="{{ item[2] if item else '' }}" required>
  <button>{% if item %}Salvar{% else %}Adicionar{% endif %}</button>
</form>
<table border="1" cellpadding="6" style="margin-top:20px;border-collapse:collapse">
<tr><th>ID</th><th>Nome</th><th>Preço</th><th>Ações</th></tr>
{% for p in produtos %}
<tr><td>{{ p[0] }}</td><td>{{ p[1] }}</td><td>R$ {{ p[2] }}</td>
<td><a href="/?editar={{ p[0] }}">Editar</a>
<form method="post" action="/excluir/{{ p[0] }}" style="display:inline"><button>Excluir</button></form></td></tr>
{% endfor %}
</table></body></html>
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