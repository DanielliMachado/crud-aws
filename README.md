# crud-aws

API REST de produtos e vendas em **Node.js (Express) + PostgreSQL**, com documentação **Swagger**, e deploy na AWS (EC2 + RDS PostgreSQL + Nginx) — Trabalho 1 de Infraestrutura Cloud, UNESC.

> A versão 1 era um app Flask com telas HTML. A versão 2 mantém **as mesmas tabelas e a mesma lógica** (cadastro de produtos, vendas com baixa de estoque em transação), mas agora é só backend: endpoints HTTP livres (sem autenticação) e um Swagger para testá-los.

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| GET | `/docs` | Swagger UI (`/` redireciona pra cá) |
| GET | `/openapi.json` | Especificação OpenAPI |
| GET | `/health` | Verifica API + conexão com o banco |
| GET | `/produtos` | Lista produtos |
| GET | `/produtos/{id}` | Busca um produto |
| POST | `/produtos` | Cria produto `{ nome, preco, quantidade }` |
| PUT | `/produtos/{id}` | Atualiza produto `{ nome, preco, quantidade }` |
| DELETE | `/produtos/{id}` | Exclui produto |
| GET | `/vendas` | Histórico de vendas com itens |
| GET | `/vendas/resumo` | Quantidade de vendas e total vendido |
| GET | `/vendas/{id}` | Busca uma venda |
| POST | `/vendas` | Registra venda `{ itens: [{ produto_id, quantidade }] }` — tudo ou nada; 409 se faltar estoque |

## Tabelas

Criadas automaticamente ao iniciar (`CREATE TABLE IF NOT EXISTS`), idênticas às da versão Flask — um banco já existente é reaproveitado sem perder dados.

- `produtos (id, nome, preco, quantidade)`
- `vendas (id, data, valor_total)`
- `itens_venda (id, venda_id → vendas, produto_id → produtos, produto_nome, quantidade, preco_unitario)`

## Rodando localmente

Requisitos: Node.js 18+ e um PostgreSQL acessível.

```bash
npm install
cp .env.example .env   # edite com os dados do seu banco
npm start
```

Abra http://localhost:3000/docs.

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta HTTP da API |
| `DB_HOST` | — | Host do PostgreSQL (endpoint do RDS em produção) |
| `DB_PORT` | `5432` | Porta do PostgreSQL |
| `DB_NAME` | `crud` | Nome do banco |
| `DB_USER` | — | Usuário |
| `DB_PASS` | — | Senha |
| `DB_SSL` | auto | `true` automaticamente quando o host é `*.rds.amazonaws.com` |

---

## Migração na AWS (Flask → Node)

O RDS **não muda**: mesmo banco, mesmas tabelas, mesmos dados. O que muda é o que roda no EC2 — sai Python/Gunicorn, entra Node.js — e o Nginx passa a apontar pra porta do Node.

Os comandos têm versão para **Ubuntu** (usuário `ubuntu`) e **Amazon Linux 2023** (usuário `ec2-user`). Use a do seu EC2.

### 1. Conectar no EC2

```bash
ssh -i sua-chave.pem ubuntu@IP-PUBLICO-DO-EC2      # Ubuntu
ssh -i sua-chave.pem ec2-user@IP-PUBLICO-DO-EC2    # Amazon Linux
```

### 2. Descobrir como o Flask roda hoje e anotar as variáveis do banco

```bash
systemctl list-units --type=service | grep -iE "gunicorn|flask|crud"
sudo systemctl cat NOME-DO-SERVICO      # mostra o ExecStart e onde estão DB_HOST/DB_USER/DB_PASS
```

Anote `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS` (podem estar no próprio service, num `EnvironmentFile=` ou num `.env` na pasta do projeto). Anote também a pasta do projeto (`WorkingDirectory=`).

### 3. Parar e desabilitar o Flask

```bash
sudo systemctl stop NOME-DO-SERVICO
sudo systemctl disable NOME-DO-SERVICO
```

### 4. Instalar o Node.js 20

```bash
# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Amazon Linux 2023
sudo dnf install -y nodejs20
sudo alternatives --install /usr/bin/node node /usr/bin/node-20 90 || true
```

Confira: `node -v` (deve ser v20.x) e `npm -v`.

### 5. Atualizar o código

Se a pasta do projeto no EC2 é um clone do GitHub:

```bash
cd /caminho/do/projeto
git pull
```

Se não for (ou der conflito), clone de novo numa pasta limpa:

```bash
cd ~
git clone https://github.com/SEU-USUARIO/crud-aws.git
cd crud-aws
```

Depois instale as dependências:

```bash
npm install --omit=dev
```

### 6. Criar o `.env` no servidor

```bash
cp .env.example .env
nano .env
```

Preencha com os valores anotados no passo 2 e use `PORT=3000`. O `.env` está no `.gitignore`, então a senha não vai pro GitHub.

Teste na mão:

```bash
npm start
# em outro terminal ssh:
curl http://localhost:3000/health     # esperado: {"status":"ok","banco":"ok"}
```

`Ctrl+C` pra parar. Se der erro de conexão, veja a seção **Problemas comuns**.

### 7. Criar o serviço systemd do Node

Troque `ubuntu` e o caminho se o seu usuário/pasta forem outros (`which node` mostra o caminho do node):

```bash
sudo tee /etc/systemd/system/crud-api.service > /dev/null <<'EOF'
[Unit]
Description=CRUD AWS - API Node.js
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/crud-aws
ExecStart=/usr/bin/node src/server.js
EnvironmentFile=/home/ubuntu/crud-aws/.env
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now crud-api
sudo systemctl status crud-api
journalctl -u crud-api -f        # logs ao vivo (Ctrl+C sai)
```

### 8. Apontar o Nginx para o Node

Encontre o arquivo do site:

```bash
grep -rl proxy_pass /etc/nginx/
```

(Ubuntu costuma ser `/etc/nginx/sites-available/...`; Amazon Linux, `/etc/nginx/conf.d/...` ou o próprio `/etc/nginx/nginx.conf`.)

Edite com `sudo nano ARQUIVO` e deixe o bloco `location /` assim — o que mudar é só o destino do `proxy_pass` (antes apontava pro Gunicorn, ex. `127.0.0.1:8000` ou um `.sock`):

```nginx
location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Valide e recarregue:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Testar de fora

No navegador: `http://IP-PUBLICO-DO-EC2/docs`. Teste `GET /produtos` — os produtos cadastrados na versão Flask devem aparecer.

### 10. Security Groups (normalmente não muda nada)

- **EC2**: continua só a porta **80** (e 22 para SSH) aberta. Não é preciso abrir a 3000, o Nginx faz a ponte.
- **RDS**: continua aceitando a porta **5432** vinda do Security Group do EC2.

### 11. Limpeza opcional

Depois de tudo funcionando: remova o service antigo (`sudo rm /etc/systemd/system/NOME-DO-SERVICO.service && sudo systemctl daemon-reload`) e a pasta `venv/` antiga.

### Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `no pg_hba.conf entry ... no encryption` | RDS exige SSL | Coloque `DB_SSL=true` no `.env` |
| `ETIMEDOUT` / `ECONNREFUSED` ao conectar no banco | Security Group do RDS | Liberar 5432 a partir do SG do EC2 |
| `password authentication failed` | Usuário/senha errados no `.env` | Conferir com os do service antigo |
| `502 Bad Gateway` no navegador | Node parado ou porta errada | `sudo systemctl status crud-api`, conferir `PORT` e `proxy_pass` |
| `database "crud" does not exist` | Banco com outro nome | Ajustar `DB_NAME` |
