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
    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = request.form.get('preco')
        quantidade = request.form.get('quantidade')
        categoria = request.form.get('categoria')
        subcategoria = request.form.get('subcategoria')
        tamanho = request.form.get('tamanho')
        data_chegada = request.form.get('data_chegada')

        # Validações básicas
        if not nome or not preco or not categoria or quantidade is None or not data_chegada:
            flash('Nome, preço, quantidade, categoria e data de chegada são obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_produto'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO produtos (nome, preco, quantidade, categoria, subcategoria, tamanho, data_chegada, usuario_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (nome, preco, quantidade, categoria, subcategoria, tamanho, data_chegada, session['usuario_id'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Produto cadastrado com sucesso!')
            return redirect(url_for('main_bp.cadastrar_produto'))
        except Exception as e:
            print("Erro ao cadastrar produto:", e)
            flash('Erro ao cadastrar produto.')
            return redirect(url_for('main_bp.cadastrar_produto'))

    return render_template('cadastrar_produto.html')

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

    nomes = []
    previsoes = []

    for produto in produtos:
        nomes.append(produto['nome'])
        previsoes.append(100)  # Número fictício por enquanto

    cursor.close()
    conn.close()
    return render_template('ver_previsao.html', nomes=nomes, previsoes=previsoes)

@main_bp.route('/ver_estoque')
@login_required
def ver_estoque():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos WHERE usuario_id = %s", (session['usuario_id'],))
    produtos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("ver_estoque.html", produtos=produtos)

@main_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id = %s", (session["usuario_id"],))
    categorias = [row['categoria'] for row in cursor.fetchall()]

    produtos = []
    vendas = []

    categoria_selecionada = request.form.get("categoria")
    produto_selecionado = request.form.get("produto")

    if categoria_selecionada:
        cursor.execute("SELECT * FROM produtos WHERE categoria = %s AND usuario_id = %s", (categoria_selecionada, session["usuario_id"]))
        produtos = cursor.fetchall()

    if produto_selecionado:
        # Aqui colocaremos a previsão manual
        previsao = 100  # Número fictício por enquanto
        cursor.execute("""
            SELECT p.nome, SUM(iv.quantidade) as total_vendido
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            JOIN vendas v ON iv.venda_id = v.id
            WHERE p.id = %s AND v.usuario_id = %s
            GROUP BY p.id
        """, (produto_selecionado, session["usuario_id"]))
        vendas = cursor.fetchall()
    else:
        previsao = None

    cursor.close()
    conn.close()
    return render_template("dashboard.html", categorias=categorias, produtos=produtos, vendas=vendas, previsao=previsao)
