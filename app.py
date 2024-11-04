from flask import Flask, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, db
from firebase_admin import firestore
from functools import wraps
import pandas as pd
import os

# Inicializa o Firebase
cred = credentials.Certificate('C:/Users/adria/OneDrive/Área de Trabalho/Prof_Escolas/credentials.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://professores-em-default-rtdb.firebaseio.com/'
})

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Use uma chave secreta para a sessão

# Decorador de login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'consultor_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']
        consultor_id = check_login(username, senha)

        if consultor_id:
            session['consultor_id'] = consultor_id
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash("Usuário ou senha incorretos", "error")
    return render_template('login.html')

def check_login(username, senha):
    # Verifica os consultores no Firebase
    ref = db.reference('consultores')
    consultores = ref.get()

    if isinstance(consultores, dict):
        for consultor_id, consultor in consultores.items():
            if consultor.get('username') == username and consultor.get('senha') == senha:
                return consultor_id
    return None

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo enviado', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
            for _, row in df.iterrows():
                escola_data = {
                    'cidade': row['cidade'],
                    'consultor_id': row['consultor_id'],
                    'inep': row['inep'],
                    'nome': row['nome'],
                    'uf': row['uf']
                }
                # Salvar no Firebase
                db.reference(f'escolas/{row["nome"]}').set(escola_data)
            
            flash('Relação de escolas carregada com sucesso!', 'success')
            return redirect(url_for('upload'))
        else:
            flash('Formato de arquivo inválido. Por favor, envie um arquivo .xlsx', 'danger')
    
    return render_template('upload.html')

@app.route('/home')
@login_required
def home():
    consultor_id = session['consultor_id']
    escolas = get_schools(consultor_id)
    return render_template('home.html', username=session['username'], escolas=escolas)

def get_schools(consultor_id):
    # Busca as escolas associadas ao consultor no Firebase
    ref = db.reference('escolas')
    escolas = ref.order_by_child('consultor_id').equal_to(consultor_id).get()
    return [escola for escola in escolas.values()] if escolas else []

@app.route('/escola/<escola_id>', methods=['GET', 'POST'])
@login_required
def professores(escola_id):
    disciplinas = [
        "Matemática", "Geografia", "História", "Filosofia", "Sociologia",
        "Biologia", "Física", "Química", "Arte", "Português",
        "Redação", "Inglês", "Espanhol", "Educação Física", "Educação Digital"
    ]
    
    ref = db.reference(f'professores/{escola_id}')
    professores_registrados = ref.get() or {}

    if request.method == 'POST':
        errors = []
        for disciplina in disciplinas:
            quantidade = request.form.get(disciplina, '')
            if quantidade.isdigit():
                ref.child(disciplina).set({'quantidade': int(quantidade)})
            else:
                errors.append(disciplina)

        if errors:
            flash(f"Entradas inválidas para: {', '.join(errors)}. Por favor, insira números válidos.", "error")
        else:
            flash("Informações salvas com sucesso!", "success")

    return render_template('professores.html', escola_id=escola_id, disciplinas=disciplinas, professores=professores_registrados)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
