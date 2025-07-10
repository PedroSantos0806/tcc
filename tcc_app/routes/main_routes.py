from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from tcc_app.utils import login_required
from tcc_app.db import get_db_connection

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
@login_required
def home():
    return render_template('home.html', nome=session.get('usuario_nome'))

@main_bp.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()

    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = request.form.get('preco')
        categoria_id = request.form.get('categoria_id')
        subcategoria_id = request.form.get('subcategoria_id')
        tamanho = request.form.get('tamanho')
        data_chegada = request.form.get('data_chegada')

        if not nome or not preco or not categoria_id or not subcategoria_id or not data_chegada:
            flash('Todos os campos são obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_produto'))

        try:
            cursor.execute(
                "INSERT INTO produtos (nome, preco, categoria_id, subcategoria_id, tamanho, data_chegada, usuario_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (nome, preco, categoria_id, subcategoria_id, tamanho, data_chegada, session['usuario_id'])
            )
            conn.commit()
            flash('Produto cadastrado com sucesso!')
            return redirect(url_for('main_bp.cadastrar_produto'))
        except Exception as e:
            print("Erro ao cadastrar produto:", e)
            conn.rollback()
            flash('Erro ao cadastrar produto.')
            return redirect(url_for('main_bp.cadastrar_produto'))

    cursor.close()
    conn.close()
    return render_template('cadastrar_produto.html', categorias=categorias)

@main_bp.route('/cadastrar_venda', methods=['GET', 'POST'])
@login_required
def cadastrar_venda():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM produtos WHERE usuario_id = %s", (session['usuario_id'],))
    produtos = cursor.fetchall()

    if request.method == 'POST':
        produto_id = request.form.get('produto_id')
        quantidade = request.form.get('quantidade')
        data_venda = request.form.get('data_venda')

        if not produto_id or not quantidade or not data_venda:
            flash('Todos os campos são obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_venda'))

        try:
            cursor.execute("SELECT preco FROM produtos WHERE id = %s", (produto_id,))
            produto = cursor.fetchone()

            if not produto:
                flash('Produto não encontrado.')
                return redirect(url_for('main_bp.cadastrar_venda'))

            preco = produto['preco']

            # Inserir venda
            cursor.execute(
                "INSERT INTO vendas (usuario_id, produto_id, quantidade, preco, data) "
                "VALUES (%s, %s, %s, %s, %s)",
                (session['usuario_id'], produto_id, quantidade, preco, data_venda)
            )
            conn.commit()
            flash('Venda registrada com sucesso!')
            return redirect(url_for('main_bp.cadastrar_venda'))
        except Exception as e:
            print("Erro ao registrar venda:", e)
            conn.rollback()
            flash('Erro ao registrar venda.')
            return redirect(url_for('main_bp.cadastrar_venda'))

    cursor.close()
    conn.close()
    return render_template('registrar_venda.html', produtos=produtos)

@main_bp.route('/ver_previsao')
@login_required
def ver_previsao():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM produtos WHERE usuario_id = %s", (session['usuario_id'],))
    produtos = cursor.fetchall()

    # Exemplo fictício de previsão
    for produto in produtos:
        produto['previsao'] = 100  # Aqui depois substitui pelo modelo real

    cursor.close()
    conn.close()
    return render_template('ver_previsao.html', produtos=produtos)
