from flask import Blueprint, render_template, redirect, url_for, request, session
from ..db import get_db_connection

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE nome = %s AND senha = %s", (usuario, senha))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['usuario'] = user['nome']
            session['usuario_id'] = user['id']
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos')

    return render_template('login.html')

@auth_routes.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        email = request.form.get('email')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, senha, email) VALUES (%s, %s, %s)", (usuario, senha, email))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('auth.login'))

    return render_template('cadastro.html')

@auth_routes.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
