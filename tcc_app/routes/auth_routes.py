from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from tcc_app.db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import os, csv

auth_bp = Blueprint('auth_bp', __name__)

def _csv_path(name: str) -> str:
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'data')
    return os.path.join(base, name)

def _find_user_in_csv(email: str):
    path = _csv_path('users.csv')
    if not os.path.exists(path): return None
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if (row.get('email', '') or '').strip().lower() == email.lower():
                return row
    return None

@auth_bp.route('/set_lang/<code>')
def set_lang(code):
    code = (code or 'pt').lower()
    if code not in ('pt', 'en', 'es'): code = 'pt'
    session['lang'] = code
    ref = request.headers.get('Referer')
    return redirect(ref or url_for('auth_bp.login'))

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
                conn = get_db_connection(); cur = conn.cursor(dictionary=True)
                cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
                usuario_db = cur.fetchone()
                cur.close(); conn.close()
            except Exception as e:
                print("Erro DB login:", e)

            def _do_login(sess_id, nome, email_, tenant_vertical=None):
                session.clear()
                session['usuario_id'] = sess_id
                session['usuario_nome'] = nome
                session['usuario_email'] = email_
                if tenant_vertical:
                    session['vertical'] = tenant_vertical
                if remember:
                    session.permanent = True
                if session.get('lang_prefill') and not session.get('lang'):
                    session['lang'] = session.pop('lang_prefill')
                return redirect(url_for('main_bp.home'))

            if usuario_db:
                if check_password_hash(usuario_db['senha'], senha):
                    # tenta descobrir vertical via tenants (se existir)
                    tenant_vertical = None
                    try:
                        conn = get_db_connection(); cur = conn.cursor(dictionary=True)
                        cur.execute("""
                            SELECT t.vertical FROM tenants t
                            JOIN usuarios u ON u.tenant_id = t.id
                            WHERE u.id = %s
                        """, (usuario_db['id'],))
                        r = cur.fetchone()
                        if r: tenant_vertical = r.get('vertical')
                        cur.close(); conn.close()
                    except Exception:
                        pass
                    return _do_login(usuario_db['id'], usuario_db['nome'], usuario_db['email'], tenant_vertical)
                else:
                    erro = 'E-mail ou senha incorretos.'
            else:
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
                        return _do_login(uid, row.get('nome') or 'Usuário', row.get('email') or email)
                if not erro:
                    erro = 'E-mail ou senha incorretos.'
    return render_template('login.html', erro=erro)

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    erro = None
    if request.method == 'POST':
        nome = (request.form.get('nome') or '').strip()
        email = (request.form.get('email') or '').strip()
        senha = (request.form.get('senha') or '').strip()
        biz_type = (request.form.get('biz_type') or 'general').strip()
        lang = (request.form.get('lang') or 'pt').strip()
        if lang not in ('pt','en','es'): lang = 'pt'
        if biz_type not in ('general','market','apparel','restaurant','electronics'):
            biz_type = 'general'

        if not nome or not email or not senha:
            erro = 'Todos os campos são obrigatórios.'
        elif len(senha) < 6:
            erro = 'A senha deve ter no mínimo 6 caracteres.'
        else:
            try:
                conn = get_db_connection(); cur = conn.cursor(dictionary=True)
                cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                existe = cur.fetchone()
                if existe:
                    erro = 'E-mail já cadastrado.'
                else:
                    # tenta criar tenant; se tabela não existir, segue fluxo normal
                    tenant_id = None
                    try:
                        slug = email.split("@",1)[0].replace(".","-").lower()
                        cur.execute("""
                            INSERT INTO tenants (name, slug, vertical, settings)
                            VALUES (%s, %s, %s, JSON_OBJECT('lang', %s))
                        """, (f"{nome.split()[0]}'s Workspace", slug, biz_type, lang))
                        tenant_id = cur.lastrowid
                    except Exception as te:
                        # sem tenants (sem migração) — ignora
                        tenant_id = None

                    hash_senha = generate_password_hash(senha)
                    if tenant_id:
                        cur.execute("""
                            INSERT INTO usuarios (nome, email, senha, tenant_id)
                            VALUES (%s, %s, %s, %s)
                        """, (nome, email, hash_senha, tenant_id))
                    else:
                        cur.execute("""
                            INSERT INTO usuarios (nome, email, senha)
                            VALUES (%s, %s, %s)
                        """, (nome, email, hash_senha))

                    conn.commit(); cur.close(); conn.close()

                    session['lang_prefill'] = lang
                    session['biz_type_prefill'] = biz_type
                    flash('Conta criada com sucesso! Faça login.')
                    return redirect(url_for('auth_bp.login'))
                cur.close(); conn.close()
            except Exception as e:
                print("Erro ao cadastrar:", str(e))
                erro = 'Erro ao cadastrar usuário. Tente novamente.'
    return render_template('cadastro.html', erro=erro)

@auth_bp.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        if not email:
            flash('Informe um e-mail.')
            return redirect(url_for('auth_bp.esqueci_senha'))
        try:
            conn = get_db_connection(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            usuario = cur.fetchone()
            cur.close(); conn.close()
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
    email = (request.form.get('email') or '').strip()
    senha = (request.form.get('senha') or '').strip()
    if not email or not senha:
        flash('Dados insuficientes.')
        return redirect(url_for('auth_bp.esqueci_senha'))
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario = cur.fetchone()
        if not usuario:
            flash('E-mail não encontrado.'); cur.close(); conn.close()
            return redirect(url_for('auth_bp.esqueci_senha'))
        hash_senha = generate_password_hash(senha)
        cur.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (hash_senha, email))
        conn.commit(); cur.close(); conn.close()
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
