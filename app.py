from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# Uma chave secreta para que as mensagens de erro (flash) funcionem sem quebrar o Flask
app.secret_key = 'segredo_profundo_da_clinica'

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    # Convertendo para minúsculo
    usuario = request.form.get('usuario').lower()
    senha = request.form.get('senha')
    papel_falso = request.form.get('papel') 
    
    # Admin tem acesso a tudo dependendo do que escolher na lista
    if usuario == "admin" and senha == "ufrj123":
        if papel_falso == 'medico':
            return redirect(url_for('interface_medico'))
        elif papel_falso == 'secretaria':
            return redirect(url_for('secretaria_recepcao'))
        elif papel_falso == 'limpeza':
            return redirect(url_for('interface_limpeza'))
            
    # usuario dentista padrão para demo
    elif usuario == "dentista" and senha == "motor123":
        return redirect(url_for('interface_medico'))
        
    # usuario secretaria padrão para demo
    elif usuario == "secretaria" and senha == "balcao123":
        return redirect(url_for('secretaria_recepcao'))
        
    # usuario paciente padrão para demo
    elif usuario == "emanuelle" and senha == "paciente123":
        return redirect(url_for('ficha_paciente'))
        
    else:
        flash("Credenciais inválidas. Tente novamente.")
        return redirect(url_for('login'))

@app.route('/medico')
def interface_medico():
    # Fingindo que temos dados vindos de um banco real para preencher a tela KKK
    pacientes_espera = [
        {"id": 1, "nome": "Carlos Silva", "procedimento": "Dentística - Restauração Resina", "horario": "14:00"},
        {"id": 2, "nome": "Ana Souza", "procedimento": "Periodontia - Raspagem", "horario": "15:15"},
        {"id": 3, "nome": "Mariana Costa", "procedimento": "Exame Clínico Geral", "horario": "16:30"}
    ]
    return render_template('interface_medico.html', pacientes=pacientes_espera)

@app.route('/secretaria')
def secretaria_recepcao():
    # Fingindo que a recepção funciona KKKK
    pacientes_clinica = [
        {"id": 1, "nome": "Carlos Silva", "telefone": "(21) 99999-9999", "status": "Aguardando"},
        {"id": 2, "nome": "Ana Souza", "telefone": "(21) 88888-8888", "status": "Em atendimento"},
        {"id": 3, "nome": "Mariana Costa", "telefone": "(21) 77777-7777", "status": "Agendada"}
    ]
    return render_template('secretaria_recepcao.html', pacientes=pacientes_clinica)

@app.route('/limpeza')
def interface_limpeza():
    return "Painel da Limpeza em construção. Alguém precisa limpar essa bagunça."

if __name__ == '__main__':
    app.run(debug=True)