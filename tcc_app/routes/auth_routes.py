from flask import Blueprint, render_template, request, redirect, url_for, session, flash
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
                    flash(f'Bem-vindo(a), {usuario["nome"]}!')
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
                    flash('Conta criada com sucesso! Faça login.')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('auth_bp.login'))
                cursor.close()
                conn.close()
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
            cursor.close()
            conn.close()

            if not usuario:
                flash('E-mail não cadastrado.')
                return redirect(url_for('auth_bp.esqueci_senha'))
            else:
                # protótipo: vai direto à tela de redefinição
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
            cursor.close()
            conn.close()
            return redirect(url_for('auth_bp.esqueci_senha'))

        hash_senha = generate_password_hash(senha)
        cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (hash_senha, email))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Senha atualizada com sucesso! Faça login.')
        return redirect(url_for('auth_bp.login'))
    except Exception as e:
        print("Erro ao redefinir senha:", str(e))
        flash('Erro ao atualizar senha. Tente novamente.')
        return redirect(url_for('auth_bp.esqueci_senha'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.')
    return redirect(url_for('auth_bp.login'))
