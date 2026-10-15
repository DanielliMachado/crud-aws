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
        cur.execute("ALTER TABLE produtos ADD COLUMN IF NOT EXISTS quantidade INTEGER NOT NULL DEFAULT 0")
        cur.execute("""CREATE TABLE IF NOT EXISTS vendas (
            id SERIAL PRIMARY KEY,
            data TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            valor_total NUMERIC(10,2) NOT NULL DEFAULT 0)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS itens_venda (
            id SERIAL PRIMARY KEY,
            venda_id INTEGER NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
            produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL,
            produto_nome VARCHAR(100) NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario NUMERIC(10,2) NOT NULL)""")

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
  .menu { margin-top: 14px; display: flex; gap: 8px; justify-content: center; }
  .menu a { color: #fff; text-decoration: none; padding: 7px 16px; border-radius: 999px; background: rgba(255,255,255,.12); font-size: 14px; font-weight: 600; }
  .menu a:hover { background: #ff9900; color: #232f3e; }
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
  <nav class="menu"><a href="/">Produtos</a><a href="/vendas">Vendas</a></nav>
</header>
<main>
  <div class="card">
    <h2>{% if item %}Editar produto #{{ item[0] }}{% else %}Novo produto{% endif %}</h2>
    <form class="cadastro" method="post" action="{% if item %}/editar/{{ item[0] }}{% else %}/criar{% endif %}">
      <input name="nome" placeholder="Nome do produto" value="{{ item[1] if item else '' }}" required>
      <input name="preco" type="number" step="0.01" min="0" placeholder="Preço (R$)" value="{{ item[2] if item else '' }}" required>
      <input name="quantidade" type="number" step="1" min="0" placeholder="Quantidade" value="{{ item[3] if item else '' }}" required>
      <button class="primario">{% if item %}Salvar{% else %}Adicionar{% endif %}</button>
      {% if item %}<a class="btn cancelar" href="/">Cancelar</a>{% endif %}
    </form>
  </div>
  <div class="card">
    <h2>Produtos cadastrados ({{ produtos|length }})</h2>
    <table>
      <tr><th>ID</th><th>Nome</th><th>Preço</th><th>Qtd.</th><th>Ações</th></tr>
      {% for p in produtos %}
      <tr>
        <td>{{ p[0] }}</td>
        <td>{{ p[1] }}</td>
        <td>R$ {{ "%.2f"|format(p[2])|replace(".", ",") }}</td>
        <td>{{ p[3] }}</td>
        <td class="acoes">
          <a class="btn editar" href="/?editar={{ p[0] }}">Editar</a>
          <form method="post" action="/excluir/{{ p[0] }}" onsubmit="return confirm('Excluir este produto?')">
            <button class="excluir">Excluir</button>
          </form>
        </td>
      </tr>
      {% else %}
      <tr><td colspan="5" class="vazio">Nenhum produto cadastrado ainda.</td></tr>
      {% endfor %}
    </table>
  </div>
</main>
<footer>Trabalho 1 · Infraestrutura Cloud AWS · UNESC</footer>
</body>
</html>
"""

PAGINA_VENDAS = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vendas</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Segoe UI", Arial, sans-serif; background: #f1f4f9; color: #1e293b; }
  header { background: #232f3e; color: #fff; padding: 22px 16px; text-align: center; }
  header h1 { margin: 0; font-size: 26px; }
  header p { margin: 6px 0 0; color: #ff9900; font-size: 14px; }
  .menu { margin-top: 14px; display: flex; gap: 8px; justify-content: center; }
  .menu a { color: #fff; text-decoration: none; padding: 7px 16px; border-radius: 999px; background: rgba(255,255,255,.12); font-size: 14px; font-weight: 600; }
  .menu a:hover { background: #ff9900; color: #232f3e; }
  main { max-width: 760px; margin: 28px auto; padding: 0 16px; }
  .card { background: #fff; border-radius: 12px; padding: 22px; box-shadow: 0 2px 10px rgba(0,0,0,.08); margin-bottom: 22px; }
  .card h2 { margin: 0 0 14px; font-size: 18px; }
  input { width: 90px; padding: 9px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 15px; }
  input:focus { outline: none; border-color: #ff9900; box-shadow: 0 0 0 3px rgba(255,153,0,.2); }
  button { padding: 11px 22px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; }
  .primario { background: #ff9900; color: #232f3e; }
  .primario:hover { background: #ec8b00; }
  .finalizar { display: flex; justify-content: flex-end; margin-top: 16px; }
  .aviso { padding: 12px 16px; border-radius: 8px; margin-bottom: 14px; font-size: 14px; font-weight: 600; }
  .aviso.ok { background: #dcfce7; color: #166534; }
  .aviso.erro { background: #fee2e2; color: #b91c1c; }
  .resumo { display: flex; gap: 14px; margin-bottom: 22px; }
  .numero { flex: 1; background: #232f3e; color: #fff; border-radius: 12px; padding: 18px 22px; }
  .numero span { display: block; font-size: 13px; color: #cbd5e1; text-transform: uppercase; }
  .numero b { font-size: 26px; color: #ff9900; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 13px; text-transform: uppercase; color: #64748b; padding: 10px; border-bottom: 2px solid #e2e8f0; }
  td { padding: 12px 10px; border-bottom: 1px solid #f1f5f9; }
  tr:hover td { background: #f8fafc; }
  .vazio { text-align: center; color: #94a3b8; padding: 24px; }
  footer { text-align: center; color: #94a3b8; font-size: 13px; padding-bottom: 24px; }
</style>
</head>
<body>
<header>
  <h1>Registro de Vendas</h1>
  <p>Aplicação Flask · AWS EC2 + RDS PostgreSQL</p>
  <nav class="menu"><a href="/">Produtos</a><a href="/vendas">Vendas</a></nav>
</header>
<main>
  <div class="resumo">
    <div class="numero"><span>Vendas registradas</span><b>{{ vendas|length }}</b></div>
    <div class="numero"><span>Total vendido</span><b>R$ {{ "%.2f"|format(total)|replace(".", ",") }}</b></div>
  </div>
  <div class="card">
    <h2>Nova venda</h2>
    {% if ok %}<div class="aviso ok">Venda registrada e estoque atualizado.</div>{% endif %}
    {% if erro == "estoque" %}<div class="aviso erro">Estoque insuficiente em algum produto. Nada foi vendido.</div>{% endif %}
    {% if erro == "vazio" %}<div class="aviso erro">Informe a quantidade de pelo menos um produto.</div>{% endif %}
    <form method="post" action="/vender">
      <table>
        <tr><th>Produto</th><th>Preço</th><th>Estoque</th><th>Quantidade</th></tr>
        {% for p in produtos %}
        <tr>
          <td>{{ p[1] }}</td>
          <td>R$ {{ "%.2f"|format(p[2])|replace(".", ",") }}</td>
          <td>{{ p[3] }}</td>
          <td><input name="qtd_{{ p[0] }}" type="number" step="1" min="0" max="{{ p[3] }}" placeholder="0"></td>
        </tr>
        {% else %}
        <tr><td colspan="4" class="vazio">Nenhum produto com estoque.</td></tr>
        {% endfor %}
      </table>
      <div class="finalizar"><button class="primario">Finalizar venda</button></div>
    </form>
  </div>
  <div class="card">
    <h2>Histórico de vendas</h2>
    <table>
      <tr><th>Nº</th><th>Data</th><th>Itens</th><th>Total</th></tr>
      {% for v in vendas %}
      <tr>
        <td>{{ v[0] }}</td>
        <td>{{ v[1] }}</td>
        <td>{{ v[3] }}</td>
        <td>R$ {{ "%.2f"|format(v[2])|replace(".", ",") }}</td>
      </tr>
      {% else %}
      <tr><td colspan="4" class="vazio">Nenhuma venda registrada ainda.</td></tr>
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
        cur.execute("SELECT id, nome, preco, quantidade FROM produtos ORDER BY id")
        produtos = cur.fetchall()
        item = None
        if request.args.get("editar"):
            cur.execute("SELECT id, nome, preco, quantidade FROM produtos WHERE id=%s", (request.args["editar"],))
            item = cur.fetchone()
    return render_template_string(PAGINA, produtos=produtos, item=item)

@app.route("/criar", methods=["POST"])
def criar():
    with conectar() as con, con.cursor() as cur:
        cur.execute("INSERT INTO produtos (nome, preco, quantidade) VALUES (%s, %s, %s)",
                    (request.form["nome"], request.form["preco"], request.form["quantidade"]))
    return redirect("/")

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    with conectar() as con, con.cursor() as cur:
        cur.execute("UPDATE produtos SET nome=%s, preco=%s, quantidade=%s WHERE id=%s",
                    (request.form["nome"], request.form["preco"], request.form["quantidade"], id))
    return redirect("/")

@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    with conectar() as con, con.cursor() as cur:
        cur.execute("DELETE FROM produtos WHERE id=%s", (id,))
    return redirect("/")

@app.route("/vendas")
def vendas():
    with conectar() as con, con.cursor() as cur:
        cur.execute("SELECT id, nome, preco, quantidade FROM produtos WHERE quantidade > 0 ORDER BY nome")
        produtos = cur.fetchall()
        cur.execute("""SELECT v.id,
                              to_char(v.data AT TIME ZONE 'America/Sao_Paulo', 'DD/MM/YYYY HH24:MI'),
                              v.valor_total,
                              string_agg(i.quantidade || 'x ' || i.produto_nome, ', ' ORDER BY i.id)
                       FROM vendas v
                       JOIN itens_venda i ON i.venda_id = v.id
                       GROUP BY v.id
                       ORDER BY v.id DESC""")
        lista = cur.fetchall()
        cur.execute("SELECT COALESCE(SUM(valor_total), 0) FROM vendas")
        total = cur.fetchone()[0]
    return render_template_string(PAGINA_VENDAS, produtos=produtos, vendas=lista, total=total,
                                  ok=request.args.get("ok"), erro=request.args.get("erro"))

@app.route("/vender", methods=["POST"])
def vender():
    itens = []
    for campo, valor in request.form.items():
        if campo.startswith("qtd_") and valor and int(valor) > 0:
            itens.append((int(campo[4:]), int(valor)))
    if not itens:
        return redirect("/vendas?erro=vazio")
    try:
        with conectar() as con, con.cursor() as cur:
            cur.execute("INSERT INTO vendas DEFAULT VALUES RETURNING id")
            venda_id = cur.fetchone()[0]
            total = 0
            for produto_id, qtd in itens:
                cur.execute("""UPDATE produtos SET quantidade = quantidade - %s
                               WHERE id = %s AND quantidade >= %s
                               RETURNING nome, preco""", (qtd, produto_id, qtd))
                produto = cur.fetchone()
                if produto is None:
                    raise ValueError("estoque insuficiente")
                nome, preco = produto
                cur.execute("""INSERT INTO itens_venda (venda_id, produto_id, produto_nome, quantidade, preco_unitario)
                               VALUES (%s, %s, %s, %s, %s)""", (venda_id, produto_id, nome, qtd, preco))
                total += preco * qtd
            cur.execute("UPDATE vendas SET valor_total = %s WHERE id = %s", (total, venda_id))
    except ValueError:
        return redirect("/vendas?erro=estoque")
    return redirect("/vendas?ok=1")

criar_tabela()