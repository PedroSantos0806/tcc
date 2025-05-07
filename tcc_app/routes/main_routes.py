# tcc_app/routes/main_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, session

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'usuario' in session:
        return render_template('index.html', usuario=session['usuario'])
    return redirect(url_for('auth.login'))

@main_bp.route('/previsao')
def previsao():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    return render_template('previsao.html')

@main_bp.route('/nova-venda')
def nova_venda():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    return render_template('registrar_venda.html')

@main_bp.route('/cadastrar-produto')
def cadastrar_produto():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    return render_template('cadastrar_produto.html')
