from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from tcc_app.db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from tcc_app.mailer import send_email
import os, csv

auth_bp = Blueprint('auth_bp', __name__)

# ---------------- CSV fallback (demo) ----------------
def _csv_path(name: str) -> str:
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'data')
    return os.path.join(base, name)

def _find_user_in_csv(email: str):
    path = _csv_path('users.csv')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if (row.get('email', '') or '').strip().lower() == email.lower():
                return row
    return None

# ---------------- Helpers ----------------
def _get_user_by_email_mysql(email: str):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

# ---------------- Idiomas ----------------
@auth_bp.route('/set_lang/<code>')
def set_lang(code):
    code = (code or 'pt').lower()
    if code not in ('pt', 'en', 'es'):
        code = 'pt'
    session['lang'] = code
    ref = request.headers.get('Referer')
    return redirect(ref or url_for('auth_bp.login'))

# ---------------- Login ----------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        senha = (request.form.get('senha') or '').strip()
        remember = request.form.get('remember') == '1'

        if not email or not senha:
            erro = 'Preencha todos os campos.'
        else:
            usuario_db = None
            try:
                usuario_db = _get_user_by_email_mysql(email)
            except Exception as e:
                print("Erro DB login:", e)

            def _do_login(sess_id, nome, email_, biz_type=None):
                session.clear()
                session['usuario_id'] = sess_id
                session['usuario_nome'] = nome
                session['usuario_email'] = email_
                session['vertical'] = (biz_type or 'other')
                if remember:
                    session.permanent = True
                if session.get('lang_prefill') and not session.get('lang'):
                    session['lang'] = session.pop('lang_prefill')
                return redirect(url_for('main_bp.dashboard'))

            if usuario_db:
                if check_password_hash(usuario_db['senha'], senha):
                    return _do_login(
                        usuario_db['id'],
                        usuario_db.get('nome') or 'Usuário',
                        usuario_db['email'],
                        usuario_db.get('biz_type')
                    )
                else:
                    erro = 'E-mail ou senha incorretos.'
            else:
                # CSV DEMO
                row = _find_user_in_csv(email)
                if row:
                    raw = row.get('senha', '') or ''
                    try:
                        ok = check_password_hash(raw, senha) if (raw.startswith('pbkdf2:') or raw.startswith('scrypt:')) else (raw == senha)
                    except Exception:
                        ok = (raw == senha)
                    if ok:
                        try:
                            uid = int(row.get('id') or 0) or 999999
                        except Exception:
                            uid = 999999
                        return _do_login(uid, row.get('nome') or 'Usuário',
                                         row.get('email') or email, row.get('biz_type') or 'other')
                if not erro:
                    erro = 'E-mail ou senha incorretos.'
    return render_template('login.html', erro=erro)

# ---------------- Cadastro ----------------
@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    erro = None
    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        email = (request.form.get('email') or '').strip()
        senha = (request.form.get('senha') or '').strip()
        biz_type = (request.form.get('biz_type') or '').strip() or 'other'
        lang = (request.form.get('lang') or '').strip() or 'pt'
        if lang not in ('pt', 'en', 'es'):
            lang = 'pt'

        if not nome or not email or not senha:
            erro = 'Todos os campos são obrigatórios.'
        elif len(senha) < 6:
            erro = 'A senha deve ter no mínimo 6 caracteres.'
        else:
            try:
                conn = get_db_connection()
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                existe = cur.fetchone()
                if existe:
                    erro = 'E-mail já cadastrado.'
                else:
                    hash_senha = generate_password_hash(senha)
                    cur.execute("""
                        INSERT INTO usuarios (nome, email, senha, biz_type, email_verified)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (nome, email, hash_senha, biz_type, 1))
                    conn.commit()
                    cur.close()
                    conn.close()

                    session['lang_prefill'] = lang

                    try:
                        print(f"[MAIL] Enviando boas-vindas para {email}")
                        send_email(
                            email,
                            "Bem-vindo(a) ao Prev Suite",
                            f"""
                            <div style="font-family:Arial,sans-serif">
                              <h2>Bem-vindo(a), {nome}!</h2>
                              <p>Seu cadastro no <strong>Prev Suite</strong> foi concluído com sucesso.</p>
                              <p>Tipo de negócio: <strong>{biz_type}</strong></p>
                              <p>Estamos à disposição. Bons negócios! 👋</p>
                            </div>
                            """
                        )
                    except Exception as mail_err:
                        print("Erro ao enviar e-mail de boas-vindas:", mail_err)

                    flash('Conta criada com sucesso! Faça login.')
                    return redirect(url_for('auth_bp.login'))
            except Exception as e:
                print("Erro ao cadastrar:", str(e))
                erro = 'Erro ao cadastrar usuário. Tente novamente.'
    return render_template('cadastro.html', erro=erro)

# ---------------- Esqueci a senha (AGORA: redefinição direta, sem token) ----------------
@auth_bp.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        senha = (request.form.get('senha') or '').strip()
        confirma = (request.form.get('confirmar_senha') or '').strip()

        if not email or not senha or not confirma:
            flash('Preencha todos os campos.')
            return redirect(url_for('auth_bp.esqueci_senha'))

        if len(senha) < 6:
            flash('A nova senha deve ter no mínimo 6 caracteres.')
            return redirect(url_for('auth_bp.esqueci_senha'))

        if senha != confirma:
            flash('As senhas não coincidem.')
            return redirect(url_for('auth_bp.esqueci_senha'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE usuarios SET senha=%s WHERE email=%s",
                (generate_password_hash(senha), email)
            )
            conn.commit()
            linhas = cur.rowcount
            cur.close()
            conn.close()

            if linhas == 0:
                flash('Nenhum usuário encontrado com este e-mail.')
                return redirect(url_for('auth_bp.esqueci_senha'))

            flash('Senha atualizada com sucesso! Faça login com a nova senha.')
            return redirect(url_for('auth_bp.login'))

        except Exception as e:
            print("Erro ao atualizar senha (esqueci_senha):", e)
            flash('Erro ao atualizar senha. Tente novamente.')
            return redirect(url_for('auth_bp.esqueci_senha'))

    return render_template('esqueci_senha.html')

# ---------------- Logout ----------------
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_bp.login'))
