from flask import Blueprint, render_template, request, redirect, url_for, session
from tcc_app.db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

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
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
                usuario = cursor.fetchone()
                cursor.close()
                conn.close()

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
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not nome or not email or not senha:
            erro = 'Todos os campos são obrigatórios.'
        elif len(senha) < 6:
            erro = 'A senha deve ter no mínimo 6 caracteres.'
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                if cursor.fetchone():
                    erro = 'E-mail já cadastrado.'
                else:
                    hash_senha = generate_password_hash(senha)
                    cursor.execute(
                        "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
                        (nome, email, hash_senha)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return redirect(url_for('auth_bp.login'))
            except Exception as e:
                print("Erro ao cadastrar:", str(e))
                erro = 'Erro ao cadastrar usuário. Tente novamente.'

    return render_template('cadastro.html', erro=erro)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login'))
