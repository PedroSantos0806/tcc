from flask import Blueprint, render_template, request, redirect, url_for, session

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        # Login fictício
        if usuario == 'admin' and senha == '123':
            session['usuario'] = usuario
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', erro='Credenciais inválidas')

    return render_template('login.html')

@auth_bp.route('/cadastro', methods=['GET', 'POST'], endpoint='cadastro')
def cadastro():
    if request.method == 'POST':
        novo_usuario = request.form['usuario']
        nova_senha = request.form['senha']

        # Cadastro fictício (apenas redireciona pro login)
        return redirect(url_for('auth.login'))

    return render_template('cadastro.html')

@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('auth.login'))
