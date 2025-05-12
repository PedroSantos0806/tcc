from flask import Blueprint, render_template, redirect, url_for, session, request
import plotly.graph_objs as go
import plotly.io as pio

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/previsao')
def previsao():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))  # Redireciona para o login

    dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex']
    produto_a = [10, 12, 8, 14, 11]
    produto_b = [5, 7, 6, 4, 8]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dias, y=produto_a, mode='lines+markers', name='Produto A'))
    fig.add_trace(go.Scatter(x=dias, y=produto_b, mode='lines+markers', name='Produto B'))
    fig.update_layout(title='Previsão de Vendas (Fictício)', xaxis_title='Dia', yaxis_title='Quantidade')

    grafico_html = pio.to_html(fig, full_html=False)

    return render_template('previsao.html', grafico=grafico_html)

@main_bp.route('/registrar_venda', methods=['GET', 'POST'])
def registrar_venda():
    if request.method == 'POST':
        produto = request.form['produto']
        quantidade = request.form['quantidade']
        # Aqui você pode salvar no banco, mas como é protótipo, só redirecionamos
        return redirect(url_for('main.previsao'))
    return render_template('registrar_venda.html')

@main_bp.route('/cadastrar_produto')
def cadastrar_produto():
    return render_template('cadastrar_produto.html')
