from flask import Blueprint, render_template, request, redirect, url_for, session
from models import obter_usuario_por_email, inserir_usuario
import hashlib

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        email = request.form['email']
        senha = hashlib.sha256(request.form['senha'].encode()).hexdigest()
        usuario = obter_usuario_por_email(email)
        if usuario and usuario['senha'] == senha:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            return redirect(url_for('main.home'))
        else:
            erro = 'E-mail ou senha incorretos.'
    return render_template('login.html', erro=erro)

@auth.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    erro = None
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = hashlib.sha256(request.form['senha'].encode()).hexdigest()
        if obter_usuario_por_email(email):
            erro = 'Já existe um usuário com este e-mail.'
        else:
            inserir_usuario(nome, email, senha)
            return redirect(url_for('auth.login'))
    return render_template('cadastro.html', erro=erro)

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
