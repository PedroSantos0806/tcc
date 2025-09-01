from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from tcc_app.db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import os, csv

auth_bp = Blueprint('auth_bp', __name__)

def _csv_path(name):
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'data')
    return os.path.join(base, name)

def _find_user_in_csv(email):
    path = _csv_path('users.csv')
    if not os.path.exists(path): return None
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('email','').strip().lower() == email.lower():
                return row
    return None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        if not email or not senha:
            erro = 'Preencha todos os campos.'
        else:
            # 1) Tenta DB
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
                usuario = cursor.fetchone()
                cursor.close(); conn.close()
                if usuario and check_password_hash(usuario['senha'], senha):
                    session['usuario_id'] = usuario['id']
                    session['usuario_nome'] = usuario['nome']
                    session['usuario_email'] = usuario['email']
                    return redirect(url_for('main_bp.home'))
            except Exception as e:
                print("Erro DB login:", e)

            # 2) Tenta CSV
            row = _find_user_in_csv(email)
            if row:
                raw = row.get('senha','')
                ok = False
                try:
                    # se for hash (pbkdf2/scrypt), usa check_password_hash
                    if raw.startswith('pbkdf2:') or raw.startswith('scrypt:'):
                        ok = check_password_hash(raw, senha)
                    else:
                        ok = (raw == senha)
                except Exception as _:
                    ok = (raw == senha)
                if ok:
                    # cria sessão "fake id" (id do CSV se existir)
                    try:
                        session['usuario_id'] = int(row.get('id') or 0) or 999999
                    except:
                        session['usuario_id'] = 999999
                    session['usuario_nome'] = row.get('nome') or 'Usuário'
                    session['usuario_email'] = row.get('email') or email
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
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                existe = cursor.fetchone()
                if existe:
                    erro = 'E-mail já cadastrado.'
                else:
                    hash_senha = generate_password_hash(senha)
                    cursor.execute(
                        "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
                        (nome, email, hash_senha)
                    )
                    conn.commit()
                    cursor.close(); conn.close()
                    flash('Conta criada com sucesso! Faça login.')
                    return redirect(url_for('auth_bp.login'))
                cursor.close(); conn.close()
            except Exception as e:
                print("Erro ao cadastrar:", str(e))
                erro = 'Erro ao cadastrar usuário. Tente novamente.'
    return render_template('cadastro.html', erro=erro)

@auth_bp.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Informe um e-mail.')
            return redirect(url_for('auth_bp.esqueci_senha'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            cursor.close(); conn.close()
            if not usuario:
                flash('Se este e-mail existir no sistema, você receberá instruções.')
                return redirect(url_for('auth_bp.esqueci_senha'))
            else:
                return render_template('resetar_senha.html', email=email)
        except Exception as e:
            print("Erro ao verificar e-mail:", str(e))
            flash('Erro ao processar. Tente novamente.')
            return redirect(url_for('auth_bp.esqueci_senha'))
    return render_template('esqueci_senha.html')

@auth_bp.route('/resetar_senha', methods=['POST'])
def resetar_senha():
    email = request.form.get('email', '').strip()
    senha = request.form.get('senha', '').strip()
    if not email or not senha:
        flash('Dados insuficientes.')
        return redirect(url_for('auth_bp.esqueci_senha'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        if not usuario:
            flash('E-mail não encontrado.')
            cursor.close(); conn.close()
            return redirect(url_for('auth_bp.esqueci_senha'))
        hash_senha = generate_password_hash(senha)
        cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (hash_senha, email))
        conn.commit()
        cursor.close(); conn.close()
        flash('Senha atualizada com sucesso! Faça login.')
        return redirect(url_for('auth_bp.login'))
    except Exception as e:
        print("Erro ao redefinir senha:", str(e))
        flash('Erro ao atualizar senha. Tente novamente.')
        return redirect(url_for('auth_bp.esqueci_senha'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login'))
