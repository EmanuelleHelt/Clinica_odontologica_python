import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = 'segredo_profundo_da_clinica'
ARQUIVO_BANCO = 'clinica_real.db'

def conectar_banco():
    conn = sqlite3.connect(ARQUIVO_BANCO)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario TEXT UNIQUE NOT NULL,
                        senha TEXT NOT NULL,
                        papel TEXT NOT NULL)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes_secretaria (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        telefone TEXT NOT NULL,
                        status TEXT NOT NULL,
                        usuario_login TEXT UNIQUE)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS fila_medico (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        procedimento TEXT NOT NULL,
                        data TEXT NOT NULL,
                        horario TEXT NOT NULL,
                        dentista_login TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS dentistas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        cro TEXT NOT NULL,
                        usuario_login TEXT UNIQUE NOT NULL)''')
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        usuarios_iniciais = [
            ('admin', 'ufrj123', 'admin'),
            ('dr.carlosantonio', '123', 'medico'),
            ('dra.anacarla', '123', 'medico'),
            ('secretaria', 'balcao123', 'secretaria'),
            ('emanuelle', 'paciente123', 'paciente')
        ]
        for u, s, p in usuarios_iniciais:
            cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, papel) VALUES (?, ?, ?)", (u, s, p))
            
        cursor.execute("INSERT INTO pacientes_secretaria (nome, telefone, status, usuario_login) VALUES (?, ?, ?, ?)", 
                       ('Emanuelle Helt', '(21) 00000-0000', 'Tremendo de medo na sala de espera', 'emanuelle'))
        conn.commit()

    # Preenchendo os doutores antigos na tabela nova para o sistema não quebrar
    cursor.execute("SELECT COUNT(*) FROM dentistas")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO dentistas (nome, cro, usuario_login) VALUES (?, ?, ?)", ('Dr. Carlos', 'CRO-RJ 12345', 'dr.carlos'))
        cursor.execute("INSERT INTO dentistas (nome, cro, usuario_login) VALUES (?, ?, ?)", ('Dra. Ana', 'CRO-RJ 67890', 'dra.ana'))
        conn.commit()

    conn.close()

inicializar_banco()

@app.route('/')
def login():
    session.clear()
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    usuario_form = request.form.get('usuario').lower()
    senha_form = request.form.get('senha')
    
    conn = conectar_banco()
    usuario_db = conn.execute('SELECT * FROM usuarios WHERE usuario = ? AND senha = ?', (usuario_form, senha_form)).fetchone()
    conn.close()
    
    if usuario_db:
        session['usuario'] = usuario_db['usuario']
        papel = usuario_db['papel']
        if papel == 'admin': return redirect(url_for('painel_admin'))
        if papel == 'medico': return redirect(url_for('interface_medico'))
        if papel == 'secretaria': return redirect(url_for('secretaria_recepcao'))
        if papel == 'paciente': return redirect(url_for('ficha_paciente'))
    else:
        flash("Credenciais inválidas. O sistema não o reconhece, intruso.")
        return redirect(url_for('login'))

@app.route('/admin')
def painel_admin():
    return render_template('admin_dashboard.html')

@app.route('/medico')
def interface_medico():
    if 'usuario' not in session: return redirect(url_for('login'))
    dentista_logado = session['usuario']
    conn = conectar_banco()
    
    data_atual = date.today().strftime('%Y-%m-%d')
    
    # Obliterando os pacientes de ontem
    pacientes_espera = conn.execute('''
        SELECT * FROM fila_medico 
        WHERE dentista_login = ? AND data >= ? 
        ORDER BY data ASC, horario ASC
    ''', (dentista_logado, data_atual)).fetchall()
    
    info_dentista = conn.execute('SELECT nome FROM dentistas WHERE usuario_login = ?', (dentista_logado,)).fetchone()
    nome_exibicao = info_dentista['nome'] if info_dentista else dentista_logado

    conn.close()
    return render_template('interface_medico.html', pacientes=pacientes_espera, dentista=nome_exibicao)

@app.route('/secretaria')
def secretaria_recepcao():
    termo_pesquisa = request.args.get('pesquisa', '')
    conn = conectar_banco()
    if termo_pesquisa:
        pacientes_clinica = conn.execute('''
            SELECT * FROM pacientes_secretaria 
            WHERE nome LIKE ? OR telefone LIKE ?
        ''', (f'%{termo_pesquisa}%', f'%{termo_pesquisa}%')).fetchall()
    else:
        pacientes_clinica = conn.execute('SELECT * FROM pacientes_secretaria').fetchall()
    conn.close()
    return render_template('secretaria_recepcao.html', pacientes=pacientes_clinica, termo=termo_pesquisa)

@app.route('/secretaria/consultas')
def secretaria_consultas():
    termo_pesquisa = request.args.get('pesquisa', '')
    conn = conectar_banco()
    
    # Capturando o exato momento em que você existe
    data_atual = date.today().strftime('%Y-%m-%d')
    
    query_base = '''
        SELECT f.*, d.nome as dentista_nome 
        FROM fila_medico f
        JOIN dentistas d ON f.dentista_login = d.usuario_login
        WHERE f.data >= ?
    '''
    
    if termo_pesquisa:
        consultas_agendadas = conn.execute(query_base + '''
            AND (f.nome LIKE ? OR f.procedimento LIKE ? OR d.nome LIKE ?)
            ORDER BY f.data ASC, f.horario ASC
        ''', (data_atual, f'%{termo_pesquisa}%', f'%{termo_pesquisa}%', f'%{termo_pesquisa}%')).fetchall()
    else:
        consultas_agendadas = conn.execute(query_base + ' ORDER BY f.data ASC, f.horario ASC', (data_atual,)).fetchall()
        
    conn.close()
    return render_template('secretaria_consultas.html', consultas=consultas_agendadas, termo=termo_pesquisa)

@app.route('/secretaria/dentistas')
def secretaria_dentistas():
    termo_pesquisa = request.args.get('pesquisa', '')
    conn = conectar_banco()
    
    if termo_pesquisa:
        # Caçando os doutores pelo nome ou pelo registro profissional
        lista_dentistas = conn.execute('''
            SELECT d.*, u.senha 
            FROM dentistas d 
            JOIN usuarios u ON d.usuario_login = u.usuario
            WHERE d.nome LIKE ? OR d.cro LIKE ?
        ''', (f'%{termo_pesquisa}%', f'%{termo_pesquisa}%')).fetchall()
    else:
        lista_dentistas = conn.execute('''
            SELECT d.*, u.senha 
            FROM dentistas d 
            JOIN usuarios u ON d.usuario_login = u.usuario
        ''').fetchall()
        
    conn.close()
    return render_template('secretaria_dentistas.html', dentistas=lista_dentistas, termo=termo_pesquisa)

@app.route('/cadastrar_dentista', methods=['GET', 'POST'])
def cadastrar_dentista():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cro = request.form.get('cro')
        usuario_login = request.form.get('usuario_login').lower()
        senha_login = request.form.get('senha_login')
        
        conn = conectar_banco()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (usuario, senha, papel) VALUES (?, ?, 'medico')", (usuario_login, senha_login))
            cursor.execute("INSERT INTO dentistas (nome, cro, usuario_login) VALUES (?, ?, ?)", (nome, cro, usuario_login))
            conn.commit()
            flash("Mais um jaleco contratado com sucesso.")
        except sqlite3.IntegrityError:
            flash("Erro: Esse login já pertence a outra entidade. Escolha outro.")
        finally:
            conn.close()
        return redirect(url_for('secretaria_dentistas'))
    return render_template('cadastro_dentista.html')

@app.route('/editar_dentista/<int:id_dentista>', methods=['GET', 'POST'])
def editar_dentista(id_dentista):
    conn = conectar_banco()
    dentista_atual = conn.execute('SELECT * FROM dentistas WHERE id = ?', (id_dentista,)).fetchone()
    login_antigo = dentista_atual['usuario_login']
    
    if request.method == 'POST':
        nome_novo = request.form.get('nome')
        cro_novo = request.form.get('cro')
        login_novo = request.form.get('usuario_login').lower()
        senha_nova = request.form.get('senha_login')
        
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE usuarios SET usuario = ?, senha = ? WHERE usuario = ?', (login_novo, senha_nova, login_antigo))
            cursor.execute('UPDATE dentistas SET nome = ?, cro = ?, usuario_login = ? WHERE id = ?', 
                           (nome_novo, cro_novo, login_novo, id_dentista))
            # tualizando as consultas caso mude o login do doutor
            cursor.execute('UPDATE fila_medico SET dentista_login = ? WHERE dentista_login = ?', (login_novo, login_antigo))
            conn.commit()
            flash("Identidade do cirurgião reescrita nos registros.")
        except sqlite3.IntegrityError:
            flash("Erro de colisão: Esse login já existe.")
        finally:
            conn.close()
        return redirect(url_for('secretaria_dentistas'))
        
    usuario_db = conn.execute('SELECT senha FROM usuarios WHERE usuario = ?', (login_antigo,)).fetchone()
    senha_atual = usuario_db['senha'] if usuario_db else ''
    conn.close()
    return render_template('editar_dentista.html', dentista=dentista_atual, senha_atual=senha_atual)

@app.route('/cadastro_paciente', methods=['GET', 'POST'])
def cadastro_paciente():
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        status = request.form.get('status')
        usuario_login = request.form.get('usuario_login').lower()
        senha_login = request.form.get('senha_login')
        conn = conectar_banco()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (usuario, senha, papel) VALUES (?, ?, 'paciente')", (usuario_login, senha_login))
            cursor.execute("INSERT INTO pacientes_secretaria (nome, telefone, status, usuario_login) VALUES (?, ?, ?, ?)", (nome, telefone, status, usuario_login))
            conn.commit()
            flash("Paciente cadastrado com sucesso.")
        except sqlite3.IntegrityError:
            flash("Erro: Esse nome de usuário já existe.")
        finally:
            conn.close()
        return redirect(url_for('secretaria_recepcao'))
    return render_template('cadastro_paciente.html')

@app.route('/editar_paciente/<int:id_paciente>', methods=['GET', 'POST'])
def editar_paciente(id_paciente):
    conn = conectar_banco()
    paciente_current = conn.execute('SELECT * FROM pacientes_secretaria WHERE id = ?', (id_paciente,)).fetchone()
    login_antigo = paciente_current['usuario_login']
    if request.method == 'POST':
        nome_novo = request.form.get('nome')
        telefone_novo = request.form.get('telefone')
        status_novo = request.form.get('status')
        login_novo = request.form.get('usuario_login').lower()
        senha_nova = request.form.get('senha_login')
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE usuarios SET usuario = ?, senha = ? WHERE usuario = ?', (login_novo, senha_nova, login_antigo))
            cursor.execute('UPDATE pacientes_secretaria SET nome = ?, telefone = ?, status = ?, usuario_login = ? WHERE id = ?', 
                           (nome_novo, telefone_novo, status_novo, login_novo, id_paciente))
            conn.commit()
            flash("Registros atualizados.")
        except sqlite3.IntegrityError:
            flash("Erro de colisão de login.")
        finally:
            conn.close()
        return redirect(url_for('secretaria_recepcao'))
    usuario_db = conn.execute('SELECT senha FROM usuarios WHERE usuario = ?', (login_antigo,)).fetchone()
    senha_atual = usuario_db['senha'] if usuario_db else ''
    conn.close()
    return render_template('editar_paciente.html', paciente=paciente_current, senha_atual=senha_atual)

@app.route('/agendar_consulta', methods=['GET', 'POST'])
def agendar_consulta():
    if request.method == 'POST':
        nome_paciente = request.form.get('nome_paciente')
        procedimento = request.form.get('procedimento')
        data_consulta = request.form.get('data_consulta')
        horario = request.form.get('horario')
        dentista_escolhido = request.form.get('dentista_login')
        
        conn = conectar_banco()
        conflito = conn.execute('''
            SELECT * FROM fila_medico 
            WHERE data = ? AND horario = ? AND dentista_login = ?
        ''', (data_consulta, horario, dentista_escolhido)).fetchone()
        
        if conflito:
            conn.close()
            flash("Erro! Esse profissional já tem uma consulta marcada neste exato dia e horário.")
            return redirect(url_for('agendar_consulta'))
            
        cursor = conn.cursor()
        cursor.execute("INSERT INTO fila_medico (nome, procedimento, data, horario, dentista_login) VALUES (?, ?, ?, ?, ?)", 
                       (nome_paciente, procedimento, data_consulta, horario, dentista_escolhido))
        conn.commit()
        conn.close()
        flash("Consulta agendada com sucesso.")
        return redirect(url_for('secretaria_consultas'))
        
    conn = conectar_banco()
    lista_pacientes = conn.execute('SELECT nome FROM pacientes_secretaria').fetchall()
    lista_dentistas = conn.execute("SELECT * FROM dentistas").fetchall()
    conn.close()
    return render_template('agendar_consulta.html', pacientes=lista_pacientes, dentistas=lista_dentistas)

@app.route('/api/horarios_ocupados')
def horarios_ocupados():
    data = request.args.get('data')
    dentista = request.args.get('dentista')
    if not data or not dentista: return jsonify([])
    conn = conectar_banco()
    agenda = conn.execute('SELECT horario FROM fila_medico WHERE data = ? AND dentista_login = ?', (data, dentista)).fetchall()
    conn.close()
    return jsonify([row['horario'] for row in agenda])

@app.route('/paciente')
def ficha_paciente():
    if 'usuario' not in session: return redirect(url_for('login'))
    usuario_logado = session['usuario']
    conn = conectar_banco()
    paciente_db = conn.execute('SELECT * FROM pacientes_secretaria WHERE usuario_login = ?', (usuario_logado,)).fetchone()
    if not paciente_db:
        conn.close()
        return redirect(url_for('login'))
    consultas_db = conn.execute('SELECT procedimento, data, horario FROM fila_medico WHERE nome = ?', (paciente_db['nome'],)).fetchall()
    conn.close()
    return render_template('paciente_ficha.html', paciente=paciente_db, consultas=consultas_db)

@app.route('/limpeza')
def interface_limpeza():
    return "Painel da Limpeza em construção."

if __name__ == '__main__':
    app.run(debug=True)