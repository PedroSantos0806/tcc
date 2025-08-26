from flask import Blueprint, render_template, request, redirect, url_for, session
from tcc_app.utils import find_usuario_by_email, add_usuario

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()
        if not email or not senha:
            erro = 'Preencha todos os campos.'
        else:
            usuario = find_usuario_by_email(email)
            if usuario and usuario["senha"] == senha:
                session['usuario_id'] = usuario['id']
                session['usuario_nome'] = usuario['nome']
                return redirect(url_for('main_bp.home'))
            erro = 'E-mail ou senha incorretos.'
    return render_template('login.html', erro=erro)

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()
        if not nome or not email or not senha:
            erro = 'Todos os campos são obrigatórios.'
        elif len(senha) < 6:
            erro = 'A senha deve ter no mínimo 6 caracteres.'
        else:
            if find_usuario_by_email(email):
                erro = 'E-mail já cadastrado.'
            else:
                novo = add_usuario(nome, email, senha)
                if novo:
                    return redirect(url_for('auth_bp.login'))
                erro = 'Erro ao cadastrar usuário. Tente novamente.'
    return render_template('cadastro.html', erro=erro)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login'))
