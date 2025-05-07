# tcc_app/routes/auth_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, session

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        # Simulação de login
        if usuario and senha:
            session['usuario'] = usuario
            print(f'Login realizado por: {usuario}')
            return redirect(url_for('main.index'))
    return render_template('login.html')

@auth_routes.route('/logout')
def logout():
    session.pop('usuario', None)
    print('Usuário deslogado.')
    return redirect(url_for('auth.login'))
