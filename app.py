from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'viola-barbearia-secret-2024'

DB = 'barbearia.db'

# ─────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS clientes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT    NOT NULL,
                telefone  TEXT    NOT NULL UNIQUE,
                criado_em TEXT    DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS agendamentos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id   INTEGER NOT NULL,
                profissional TEXT    NOT NULL,
                servico      TEXT    NOT NULL,
                horario      TEXT    NOT NULL,
                valor        TEXT    NOT NULL,
                valor_num    REAL    DEFAULT 0,
                data         TEXT    DEFAULT (date('now','localtime')),
                criado_em    TEXT    DEFAULT (datetime('now','localtime')),
                concluido    INTEGER DEFAULT 0,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            );
        ''')
        # Adiciona colunas caso o banco já existia sem elas
        for col, tipo in [('valor_num', 'REAL DEFAULT 0'), ('concluido', 'INTEGER DEFAULT 0')]:
            try:
                conn.execute(f"ALTER TABLE agendamentos ADD COLUMN {col} {tipo}")
                conn.commit()
            except:
                pass

init_db()

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

HORARIOS = [
    '08:00','08:30','09:00','09:30','10:00','10:30',
    '11:00','11:30','13:00','13:30','14:00','14:30',
    '15:00','15:30','16:00','16:30','17:00','17:30',
]

PRECOS = {
    'Corte de Cabelo': ('R$ 30', 30.0),
    'Barba':           ('R$ 30', 30.0),
    'Corte + Barba':   ('R$ 55', 55.0),
    'Hidratação':      ('R$ 40', 40.0),
}

ADMIN_TELEFONE = '7412345678'  # ← seu número real aqui

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def formatar_reais(valor):
    return f"R$ {valor:,.0f}".replace(',', '.')

def calcular_lucro(conn, data_ini, data_fim):
    rows = conn.execute(
        '''SELECT COALESCE(SUM(valor_num), 0) AS total, COUNT(*) AS qtd
           FROM agendamentos
           WHERE data >= ? AND data <= ? AND concluido = 1''',
        (data_ini, data_fim)
    ).fetchone()
    return rows['total'], rows['qtd']

# ─────────────────────────────────────────
# LOGIN CLIENTE
# ─────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        acao     = request.form.get('acao')
        telefone = request.form.get('telefone', '').strip()

        if acao == 'entrar':
            if not telefone:
                flash('Digite seu telefone.', 'erro')
                return render_template('login.html', aba_ativa='entrar')

            with get_db() as conn:
                cliente = conn.execute(
                    'SELECT * FROM clientes WHERE telefone = ?', (telefone,)
                ).fetchone()

            if not cliente:
                flash('Número não encontrado. Crie uma conta primeiro.', 'erro')
                return render_template('login.html', aba_ativa='entrar')

            session['cliente_id']   = cliente['id']
            session['cliente_nome'] = cliente['nome']
            session['cliente_tel']  = cliente['telefone']
            return redirect(url_for('agenda'))

        elif acao == 'criar':
            nome = request.form.get('nome', '').strip()
            if not nome or not telefone:
                flash('Preencha nome e telefone.', 'erro')
                return render_template('login.html', aba_ativa='criar')

            with get_db() as conn:
                existente = conn.execute(
                    'SELECT id FROM clientes WHERE telefone = ?', (telefone,)
                ).fetchone()

                if existente:
                    flash('Número já cadastrado. Entre na aba "Entrar".', 'erro')
                    return render_template('login.html', aba_ativa='criar')

                conn.execute(
                    'INSERT INTO clientes (nome, telefone) VALUES (?, ?)',
                    (nome, telefone)
                )
                conn.commit()
                cliente = conn.execute(
                    'SELECT * FROM clientes WHERE telefone = ?', (telefone,)
                ).fetchone()

            session['cliente_id']   = cliente['id']
            session['cliente_nome'] = cliente['nome']
            session['cliente_tel']  = cliente['telefone']
            flash(f'Bem-vindo, {nome}! Conta criada com sucesso.', 'ok')
            return redirect(url_for('agenda'))

    return render_template('login.html', aba_ativa='entrar')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────────────────────
# AGENDA (CLIENTE)
# ─────────────────────────────────────────

@app.route('/agenda', methods=['GET', 'POST'])
def agenda():
    if 'cliente_id' not in session:
        return redirect(url_for('login'))

    mensagem = None
    hoje = datetime.now().strftime('%Y-%m-%d')

    with get_db() as conn:
        ocupados_rows = conn.execute(
            'SELECT horario FROM agendamentos WHERE data = ?', (hoje,)
        ).fetchall()
        ocupados = [r['horario'] for r in ocupados_rows]

    if request.method == 'POST':
        profissional = request.form.get('profissional', '').strip()
        servico      = request.form.get('servico', '').strip()
        horario      = request.form.get('horario', '').strip()

        valor_str, valor_num = PRECOS.get(servico, ('R$ 30', 30.0))

        if not horario:
            mensagem = 'Escolha um horário.'
        elif horario in ocupados:
            mensagem = 'Horário já ocupado. Escolha outro.'
        else:
            with get_db() as conn:
                conn.execute(
                    '''INSERT INTO agendamentos
                       (cliente_id, profissional, servico, horario, valor, valor_num)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (session['cliente_id'], profissional, servico, horario, valor_str, valor_num)
                )
                conn.commit()
                ocupados.append(horario)
            mensagem = 'Agendamento realizado com sucesso!'

    return render_template(
        'agendamento.html',
        horarios=HORARIOS,
        ocupados=ocupados,
        mensagem=mensagem,
        nome_cliente=session.get('cliente_nome', ''),
    )

# ─────────────────────────────────────────
# MEUS AGENDAMENTOS (CLIENTE)
# ─────────────────────────────────────────

@app.route('/meus-agendamentos')
def meus_agendamentos():
    if 'cliente_id' not in session:
        return {'erro': 'não autenticado'}, 401

    with get_db() as conn:
        ags = conn.execute(
            '''SELECT profissional, servico, horario, valor, data
               FROM agendamentos
               WHERE cliente_id = ?
               ORDER BY data DESC, horario DESC''',
            (session['cliente_id'],)
        ).fetchall()

    return {'agendamentos': [dict(a) for a in ags]}

# ─────────────────────────────────────────
# ADMIN — LOGIN
# ─────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    erro = None
    if request.method == 'POST':
        telefone = request.form.get('telefone', '').strip()
        if telefone == ADMIN_TELEFONE:
            session['admin'] = True
            return redirect(url_for('admin_painel'))
        erro = 'Número não autorizado.'
    return render_template('admin_login.html', erro=erro)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# ─────────────────────────────────────────
# ADMIN — PAINEL
# ─────────────────────────────────────────

@app.route('/admin')
def admin_painel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    hoje  = datetime.now()
    s_ini = (hoje - timedelta(days=hoje.weekday())).strftime('%Y-%m-%d')
    m_ini = hoje.strftime('%Y-%m-01')
    hoje_str = hoje.strftime('%Y-%m-%d')

    with get_db() as conn:
        val_dia,    qtd_dia    = calcular_lucro(conn, hoje_str, hoje_str)
        val_semana, qtd_semana = calcular_lucro(conn, s_ini,    hoje_str)
        val_mes,    qtd_mes    = calcular_lucro(conn, m_ini,    hoje_str)

        ags_hoje = conn.execute(
            '''SELECT a.*, c.nome AS nome_cliente, c.telefone
               FROM agendamentos a
               JOIN clientes c ON c.id = a.cliente_id
               WHERE a.data = ?
               ORDER BY a.horario ASC''',
            (hoje_str,)
        ).fetchall()

        clientes = conn.execute(
            'SELECT * FROM clientes ORDER BY criado_em DESC'
        ).fetchall()

    mapa = {row['horario']: row for row in ags_hoje}

    return render_template(
        'admin.html',
        todos_horarios        = HORARIOS,
        agendamentos_hoje     = ags_hoje,
        agendamentos_hoje_map = mapa,
        clientes              = clientes,
        lucro_dia             = formatar_reais(val_dia),
        lucro_semana          = formatar_reais(val_semana),
        lucro_mes             = formatar_reais(val_mes),
        qtd_dia               = qtd_dia,
        qtd_semana            = qtd_semana,
        qtd_mes               = qtd_mes,
    )

# ─────────────────────────────────────────
# ADMIN — CONCLUIR CORTE
# ─────────────────────────────────────────

@app.route('/admin/concluir', methods=['POST'])
def admin_concluir():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    ag_id = request.form.get('agendamento_id')
    if ag_id:
        with get_db() as conn:
            conn.execute(
                'UPDATE agendamentos SET concluido = 1 WHERE id = ?', (ag_id,)
            )
            conn.commit()
        flash('Corte marcado como concluído! Valor debitado no saldo.', 'ok')
    return redirect(url_for('admin_painel'))

# ─────────────────────────────────────────
# ADMIN — REMOVER AGENDAMENTO
# ─────────────────────────────────────────

@app.route('/admin/remover', methods=['POST'])
def admin_remover():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    ag_id = request.form.get('agendamento_id')
    if ag_id:
        with get_db() as conn:
            conn.execute('DELETE FROM agendamentos WHERE id = ?', (ag_id,))
            conn.commit()
        flash('Agendamento removido com sucesso.', 'ok')
    else:
        flash('Erro ao remover agendamento.', 'erro')

    return redirect(url_for('admin_painel'))

# ─────────────────────────────────────────
# ADMIN — RESETAR DIA
# ─────────────────────────────────────────

@app.route('/admin/resetar-dia', methods=['POST'])
def admin_resetar_dia():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    hoje = datetime.now().strftime('%Y-%m-%d')
    with get_db() as conn:
        conn.execute('DELETE FROM agendamentos WHERE data = ?', (hoje,))
        conn.commit()

    flash('Todos os horários de hoje foram resetados.', 'ok')
    return redirect(url_for('admin_painel'))

# ─────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)