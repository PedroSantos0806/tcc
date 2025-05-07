# tcc_app/routes/main_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, session
import plotly.express as px
from functools import wraps

main_bp = Blueprint('main', __name__)

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/previsao')
@login_required
def previsao():
    return render_template('previsao.html')

@main_bp.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'POST':
        nome = request.form.get('nome')
        print(f'Produto cadastrado: {nome}')
        return redirect(url_for('main.index'))
    return render_template('cadastrar_produto.html')

@main_bp.route('/registrar_venda', methods=['GET', 'POST'])
@login_required
def registrar_venda():
    if request.method == 'POST':
        produto = request.form.get('produto')
        quantidade = request.form.get('quantidade')
        print(f'Venda registrada: {quantidade}x {produto}')
        return redirect(url_for('main.index'))
    return render_template('registrar_venda.html')

@main_bp.route('/ver_previsao')
@login_required
def ver_previsao():
    dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex']
    vendas = [10, 15, 7, 12, 20]
    grafico = px.line(x=dias, y=vendas, title='Previsão de Vendas (fictícia)', labels={'x': 'Dia', 'y': 'Quantidade'})
    grafico_html = grafico.to_html(full_html=False)
    return render_template('ver_previsao.html', grafico=grafico_html)
