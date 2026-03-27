import os
from dotenv import load_dotenv

load_dotenv()

import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "barbearia-viola-secret")

DB = 'agendamentos.db'
ADMIN = os.getenv("ADMIN_TELEFONE", "7412345678")


# ── BANCO DE DADOS ─────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                servico TEXT NOT NULL,
                preco TEXT NOT NULL,
                data TEXT NOT NULL,
                horario TEXT NOT NULL,
                status TEXT DEFAULT 'confirmado',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

init_db()


# ── HORÁRIOS ───────────────────────────────────────────────────────────────────
def gerar_horarios():
    horarios = []
    hora, minuto = 7, 30
    while hora < 19 or (hora == 19 and minuto <= 30):
        horarios.append(f"{hora:02d}:{minuto:02d}")
        minuto += 30
        if minuto == 60:
            minuto = 0
            hora += 1
    return horarios

HORARIOS = gerar_horarios()


# ── LOGIN ──────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def login():
    mensagem = ""
    tipo = ""

    if request.method == "POST":
        telefone = request.form.get("telefone", "").strip()

        if telefone == ADMIN:
            session["autenticado"] = True
            return redirect(url_for("agenda"))
        else:
            mensagem = "Telefone não cadastrado!"
            tipo = "erro"

    return render_template("index.html", mensagem=mensagem, tipo=tipo)


# ── AGENDAMENTO ────────────────────────────────────────────────────────────────
@app.route("/agenda", methods=["GET", "POST"])
def agenda():
    if not session.get("autenticado"):
        return redirect(url_for("login"))

    mensagem = ""

    if request.method == "POST":
        nome        = request.form.get("nome", "").strip()
        telefone    = request.form.get("telefone", "").strip()
        profissional = request.form.get("profissional", "Qualquer")
        servico     = request.form.get("servico", "")
        preco       = request.form.get("preco", "")
        data        = request.form.get("data", "")
        horario     = request.form.get("horario", "")

        if not horario:
            mensagem = "Selecione um horário!"
        else:
            with get_db() as conn:
                # Verifica se horário já está ocupado na mesma data
                ocupado = conn.execute(
                    "SELECT 1 FROM agendamentos WHERE data = ? AND horario = ?",
                    (data, horario)
                ).fetchone()

                if ocupado:
                    mensagem = "Esse horário já foi agendado!"
                else:
                    conn.execute(
                        '''INSERT INTO agendamentos
                           (nome, telefone, servico, preco, data, horario)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        (nome, telefone, servico, preco, data, horario)
                    )
                    mensagem = "Agendamento realizado com sucesso!"

    # Busca horários ocupados do banco para o dia atual
    with get_db() as conn:
        from datetime import date
        hoje = date.today().isoformat()
        ocupados = [
            r["horario"] for r in conn.execute(
                "SELECT horario FROM agendamentos WHERE data = ?", (hoje,)
            ).fetchall()
        ]

    return render_template(
        "agendamento.html",
        horarios=HORARIOS,
        ocupados=ocupados,
        mensagem=mensagem
    )


# ── MEUS AGENDAMENTOS (API) ────────────────────────────────────────────────────
@app.route('/meus-agendamentos')
def meus_agendamentos():
    telefone = request.args.get('telefone', '').strip()

    if not telefone:
        return jsonify({'erro': 'Telefone não informado'}), 400

    with get_db() as conn:
        rows = conn.execute('''
            SELECT nome, telefone, servico, preco, data, horario, status
            FROM agendamentos
            WHERE telefone = ?
            ORDER BY criado_em DESC
        ''', (telefone,)).fetchall()

    return jsonify([dict(r) for r in rows])


# ── LOGOUT ─────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── MAIN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug)