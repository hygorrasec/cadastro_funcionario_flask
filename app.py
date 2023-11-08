from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import sqlite3

app = Flask(__name__)

app.secret_key = 'secret_key_1234567890'

def criar_banco_de_dados():
    conn = sqlite3.connect('funcionarios.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS setor (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cargos (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            id_setor INTEGER,
            FOREIGN KEY (id_setor) REFERENCES setor(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY,
            primeiro_nome TEXT NOT NULL,
            sobrenome TEXT NOT NULL,
            data_admissao DATE NOT NULL,
            status_funcionario BOOL NOT NULL DEFAULT true,
            id_setor INTEGER,
            id_cargo INTEGER,
            FOREIGN KEY (id_setor) REFERENCES setor(id),
            FOREIGN KEY (id_cargo) REFERENCES cargos(id)
        )
    ''')

    conn.commit()
    conn.close()

def adicionar_setor(conn, cursor, nome_setor):
    cursor.execute("SELECT id FROM setor WHERE nome=?", (nome_setor,))
    setor = cursor.fetchone()
    if setor is None:
        cursor.execute("INSERT INTO setor (nome) VALUES (?)", (nome_setor,))
        conn.commit()
        return cursor.lastrowid
    else:
        return setor[0]

def adicionar_cargo(conn, cursor, nome_cargo, id_setor):
    cursor.execute("SELECT id FROM cargos WHERE nome=? AND id_setor=?", (nome_cargo, id_setor))
    cargo = cursor.fetchone()
    if cargo is None:
        cursor.execute("INSERT INTO cargos (nome, id_setor) VALUES (?, ?)", (nome_cargo, id_setor))
        conn.commit()

@app.template_filter('string_to_date')
def string_to_date(value, format='%Y-%m-%d'):
    return datetime.strptime(value, format).strftime("%d/%m/%Y") if value else None

@app.route('/')
def cadastro_funcionarios():

    criar_banco_de_dados()

    conn = sqlite3.connect('funcionarios.db')
    cursor = conn.cursor()

    setores = ['TI', 'Recursos Humanos', 'Vendas']
    for setor in setores:
        adicionar_setor(conn, cursor, setor)

    cargos = [
        {'nome': 'Programador', 'setor': 'TI'},
        {'nome': 'Gerente de RH', 'setor': 'Recursos Humanos'},
        {'nome': 'Vendedor', 'setor': 'Vendas'}
    ]

    for cargo in cargos:
        setor_id = adicionar_setor(conn, cursor, cargo['setor'])
        adicionar_cargo(conn, cursor, cargo['nome'], setor_id)

    cursor.execute("SELECT id, nome FROM setor")
    setores = cursor.fetchall()

    cursor.execute("SELECT id, nome FROM cargos")
    cargos = cursor.fetchall()

    cursor.execute("""
        SELECT funcionarios.id, primeiro_nome, sobrenome, data_admissao, status_funcionario, setor.nome, cargos.nome
        FROM funcionarios
        JOIN setor ON funcionarios.id_setor = setor.id
        JOIN cargos ON funcionarios.id_cargo = cargos.id
    """)
    funcionarios = cursor.fetchall()

    funcionarios_formatados = []
    for funcionario in funcionarios:
        funcionarios_formatados.append(
            (funcionario[0], funcionario[1], funcionario[2], string_to_date(funcionario[3]), 'Ativo' if funcionario[4] else 'Inativo', funcionario[5], funcionario[6])
        )

    conn.close()

    return render_template('index.html', setores=setores, cargos=cargos, funcionarios=funcionarios)

@app.route('/index', methods=['POST'])
def index():
    primeiro_nome = request.form['primeiro_nome']
    sobrenome = request.form['sobrenome']
    id_setor = request.form['id_setor']
    id_cargo = request.form['id_cargo']

    conn = sqlite3.connect('funcionarios.db')
    cursor = conn.cursor()

    data_atual = datetime.now()
    data_admissao = data_atual.strftime('%Y-%m-%d')

    cursor.execute("INSERT INTO funcionarios (primeiro_nome, sobrenome, data_admissao, status_funcionario, id_setor, id_cargo) VALUES (?, ?, ?, ?, ?, ?)",
                   (primeiro_nome, sobrenome, data_admissao, 'true', id_setor, id_cargo))

    conn.commit()
    conn.close()

    flash('Funcionário cadastrado com sucesso!')

    return redirect(url_for('cadastro_funcionarios'))

if __name__ == '__main__':
    app.run(debug=True)
