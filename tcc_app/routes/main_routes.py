# tcc_app/routes/main_routes.py

from flask import Blueprint, render_template, session
from ..utils import login_required

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

@main_bp.route('/vendas')
@login_required
def vendas():
    return render_template('vendas.html')
