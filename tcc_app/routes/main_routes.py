from flask import Blueprint, render_template, session
from utils import login_required

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def home():
    return render_template('home.html', nome=session.get('usuario_nome'))

@main.route('/ver_previsao')
@login_required
def ver_previsao():
    return render_template('ver_previsao.html')

@main.route('/cadastrar_produto')
@login_required
def cadastrar_produto():
    return render_template('cadastrar_produto.html')

@main.route('/cadastrar_venda')
@login_required
def cadastrar_venda():
    return render_template('cadastrar_venda.html')
