import sqlite3
import random
import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'segredo_profundo_da_clinica'
ARQUIVO_BANCO = 'clinica_real.db'

# --- COMENTE AS LINHAS ABAIXO PARA PARAR DE MATAR SEUS DADOS ---
# --- AMNÉSIA FORÇADA ---
if os.path.exists(ARQUIVO_BANCO):
    os.remove(ARQUIVO_BANCO)
    print("O banco antigo foi obliterado. Iniciando do zero.")
# -------------------------------------

# --- A INFRAESTRUTURA DE VERDADE ---
def conectar_banco():
    conn = sqlite3.connect(ARQUIVO_BANCO)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco():
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes_secretaria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fila_medico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            procedimento TEXT NOT NULL,
            horario TEXT NOT NULL
        )
    ''')
    # A sua nova exigência: A tabela de usuários e papéis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            papel TEXT NOT NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM pacientes_secretaria")
    if cursor.fetchone()[0] == 0:
        injetar_dados_ficticios(conn)
        
    conn.close()

def injetar_dados_ficticios(conn):
    cursor = conn.cursor()
    
    # Injetando os logins originais para você não ficar trancada do lado de fora
    usuarios_iniciais = [
        ('admin', 'ufrj123', 'admin'),
        ('dentista', 'motor123', 'medico'),
        ('secretaria', 'balcao123', 'secretaria'),
        ('emanuelle', 'paciente123', 'paciente')
    ]
    for u, s, p in usuarios_iniciais:
        cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, papel) VALUES (?, ?, ?)", (u, s, p))
    
    nomes_base = ["Carlos", "Ana", "Mariana", "João", "Beatriz", "Fernando", "Cláudia", "Roberto", "Juliana"]
    sobrenomes = ["Silva", "Souza", "Costa", "Oliveira", "Santos", "Ferreira", "Alves", "Pereira"]
    procedimentos = ["Dentística - Restauração Resina", "Periodontia - Raspagem Subgengival", "Exame Clínico Geral", "Extração"]
    status_lista = ["Aguardando", "Em atendimento", "Agendada", "Em pânico na sala de espera"]
    
    for _ in range(8):
        nome = f"{random.choice(nomes_base)} {random.choice(sobrenomes)}"
        telefone = f"(21) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        procedimento = random.choice(procedimentos)
        horario = f"{random.randint(8,17):02d}:{random.choice(['00', '15', '30', '45'])}"
        status = random.choice(status_lista)
        
        cursor.execute("INSERT INTO fila_medico (nome, procedimento, horario) VALUES (?, ?, ?)", (nome, procedimento, horario))
        cursor.execute("INSERT INTO pacientes_secretaria (nome, telefone, status) VALUES (?, ?, ?)", (nome, telefone, status))
    
    conn.commit()
    print("Banco de dados forjado com sucesso. Incluindo as chaves de acesso.")

inicializar_banco()
# ------------------------------------------------------

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    usuario_form = request.form.get('usuario').lower()
    senha_form = request.form.get('senha')
    
    # O porteiro agora sabe ler registros oficiais
    conn = conectar_banco()
    usuario_db = conn.execute('SELECT * FROM usuarios WHERE usuario = ? AND senha = ?', (usuario_form, senha_form)).fetchone()
    conn.close()
    
    if usuario_db:
        papel = usuario_db['papel']
        
        # O filtro de rotas dinâmico que você implorou
        if papel == 'admin':
            return redirect(url_for('painel_admin'))
        elif papel == 'medico':
            return redirect(url_for('interface_medico'))
        elif papel == 'secretaria':
            return redirect(url_for('secretaria_recepcao'))
        elif papel == 'paciente':
            return redirect(url_for('ficha_paciente'))
    else:
        flash("Credenciais inválidas. O sistema não o reconhece, intruso.")
        return redirect(url_for('login'))

@app.route('/admin')
def painel_admin():
    return render_template('admin_dashboard.html')

@app.route('/medico')
def interface_medico():
    conn = conectar_banco()
    pacientes_espera = conn.execute('SELECT * FROM fila_medico').fetchall()
    conn.close()
    return render_template('interface_medico.html', pacientes=pacientes_espera)

@app.route('/secretaria')
def secretaria_recepcao():
    conn = conectar_banco()
    pacientes_clinica = conn.execute('SELECT * FROM pacientes_secretaria').fetchall()
    conn.close()
    return render_template('secretaria_recepcao.html', pacientes=pacientes_clinica)

@app.route('/limpeza')
def interface_limpeza():
    return "Painel da Limpeza em construção. Alguém precisa limpar essa bagunça."

@app.route('/paciente')
def ficha_paciente():
    dados_paciente = {
        "nome": "Emanuelle Helt",
        "idade": 21,
        "proximo_procedimento": "Avaliação de Dentística",
        "status": "Tremendo de medo na sala de espera",
        "historico": ["Limpeza Profunda - Janeiro/2026", "Restauração - Março/2026"]
    }
    return render_template('paciente_ficha.html', paciente=dados_paciente)

if __name__ == '__main__':
    app.run(debug=True)