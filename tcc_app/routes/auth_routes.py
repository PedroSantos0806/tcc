from flask import Blueprint, render_template, request, redirect, url_for, session
from tcc_app.db import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash

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
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT * FROM usuarios WHERE email=%s LIMIT 1", (email,))
                u = cur.fetchone()
                cur.close(); conn.close()
                ok = False
                if u:
                    # aceita senha em texto ou hash
                    if u['senha'].startswith('pbkdf2:') or u['senha'].startswith('scrypt:') or u['senha'].startswith('bcrypt$'):
                        ok = check_password_hash(u['senha'], senha)
                    else:
                        ok = (u['senha'] == senha)
                if ok:
                    session['usuario_id'] = u['id']
                    session['usuario_nome'] = u['nome']
                    session['usuario_email'] = u['email']
                    return redirect(url_for('main_bp.home'))
                erro = 'E-mail ou senha incorretos.'
            except Exception as e:
                print("Erro ao fazer login:", e)
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
                cur = conn.cursor()
                cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
                if cur.fetchone():
                    erro = 'E-mail já cadastrado.'
                else:
                    # por ora guardamos texto simples para compatibilidade.
                    # Se quiser hash, troque abaixo por generate_password_hash(senha)
                    cur.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s,%s,%s)",
                                (nome, email, senha))
                    conn.commit()
                    cur.close(); conn.close()
                    return redirect(url_for('auth_bp.login'))
                cur.close(); conn.close()
            except Exception as e:
                print("Erro ao cadastrar:", e)
                erro = 'Erro ao cadastrar usuário. Tente novamente.'
    return render_template('cadastro.html', erro=erro)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login'))
