from flask import Blueprint, render_template, request, redirect, url_for, session
from tcc_app.db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        email = request.form.get('email') or ''
        senha = request.form.get('senha') or ''

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            cursor.close()

            if usuario and check_password_hash(usuario['senha'], senha):
                session['usuario_id'] = usuario['id']
                session['usuario_nome'] = usuario['nome']
                return redirect(url_for('main_bp.home'))
            else:
                erro = 'E-mail ou senha incorretos.'
        except Exception as e:
            print("Erro ao fazer login:", str(e))
            erro = 'Erro interno. Tente novamente.'

    return render_template('login.html', erro=erro)

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome') or ''
        email = request.form.get('email') or ''
        senha = request.form.get('senha') or ''

        if not nome.strip() or not email.strip() or not senha.strip():
            erro = 'Todos os campos são obrigatórios.'
        else:
            try:
                hash_senha = generate_password_hash(senha)
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
                    (nome, email, hash_senha)
                )
                conn.commit()
                cursor.close()
                return redirect(url_for('auth_bp.login'))
            except Exception as e:
                print("Erro ao cadastrar:", str(e))
                erro = 'Erro ao cadastrar usuário. Verifique se o e-mail já está em uso.'

    return render_template('cadastro.html', erro=erro)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login'))
