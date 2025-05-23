# tcc_app/routes/main_routes.py

from flask import Blueprint, render_template, session, request, redirect, url_for
from ..utils import login_required
from ..models import db, Produto, Venda
from datetime import date

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html', usuario=session.get('usuario'))

@main_bp.route('/previsao')
@login_required
def previsao():
    return render_template('previsao.html')

@main_bp.route('/produtos')
@login_required
def produtos():
    return render_template('produtos.html')

@main_bp.route('/vendas', methods=['GET', 'POST'], endpoint='registrar_venda')
@login_required
def vendas():
    if request.method == 'POST':
        produto_id = request.form['produto']
        quantidade = int(request.form['quantidade'])
        data_venda = date.today()

        nova_venda = Venda(produto_id=produto_id, quantidade=quantidade, data=data_venda)
        db.session.add(nova_venda)
        db.session.commit()

        return redirect(url_for('main.registrar_venda'))

    produtos = Produto.query.filter_by(usuario_id=session.get('usuario_id')).all()
    return render_template('registrar_venda.html', produtos=produtos)

@main_bp.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        usuario_id = session.get('usuario_id')
        novo_produto = Produto(nome=nome, usuario_id=usuario_id)
        db.session.add(novo_produto)
        db.session.commit()
        return redirect(url_for('main.cadastrar_produto'))

    return render_template('cadastrar_produto.html')
