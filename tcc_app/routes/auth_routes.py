# tcc_app/routes/auth_routes.py

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from ..db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE nome = %s AND senha = %s", (usuario, senha))
        user = cursor.fetchone()

        if user:
            session['usuario'] = usuario
            return redirect(url_for('main.index'))
        else:
            flash('Usuário ou senha incorretos', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('auth.login'))
