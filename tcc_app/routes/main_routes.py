from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from tcc_app.utils import login_required
from tcc_app.db import get_db_connection, get_db
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import os

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
        preco_custo = request.form.get('preco_custo')
        preco_venda = request.form.get('preco_venda')
        quantidade = request.form.get('quantidade')
        categoria = request.form.get('categoria')
        subcategoria = request.form.get('subcategoria')
        tamanho = request.form.get('tamanho')
        data_chegada = request.form.get('data_chegada')

        if not nome or not preco or not preco_custo or not preco_venda or not categoria or quantidade is None or not data_chegada:
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_produto'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO produtos (nome, preco, preco_custo, preco_venda, quantidade, categoria, subcategoria, tamanho, data_chegada, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (nome, preco, preco_custo, preco_venda, quantidade, categoria, subcategoria, tamanho, data_chegada, session['usuario_id']))
            conn.commit()
            flash('Produto cadastrado com sucesso!')
        except Exception as e:
            print("Erro ao cadastrar produto:", e)
            flash('Erro ao cadastrar produto.')
        finally:
            cursor.close()
            conn.close()

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
        data_venda = request.form.get('data_venda')
        produto_ids = request.form.getlist('produto_id[]')
        quantidades = request.form.getlist('quantidade[]')

        if not data_venda or not produto_ids or not quantidades:
            flash("Preencha todos os campos.")
            return redirect(url_for('main_bp.cadastrar_venda'))

        try:
            cursor.execute("INSERT INTO vendas (usuario_id, data) VALUES (%s, %s)", (session['usuario_id'], data_venda))
            venda_id = cursor.lastrowid

            for produto_id, quantidade in zip(produto_ids, quantidades):
                cursor.execute("SELECT preco_venda FROM produtos WHERE id = %s", (produto_id,))
                produto = cursor.fetchone()
                preco = produto['preco_venda']

                cursor.execute("""
                    INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
                    VALUES (%s, %s, %s, %s)
                """, (venda_id, produto_id, quantidade, preco))

            conn.commit()
            flash("Venda registrada com sucesso!")
        except Exception as e:
            print("Erro ao registrar venda:", e)
            conn.rollback()
            flash("Erro ao registrar venda.")
        finally:
            cursor.close()
            conn.close()
            return redirect(url_for('main_bp.cadastrar_venda'))

    cursor.close()
    conn.close()
    return render_template("registrar_venda.html", produtos=produtos)

@main_bp.route('/ver_estoque')
@login_required
def ver_estoque():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id, p.nome, p.categoria, p.preco_venda, p.preco_custo, 
               p.quantidade AS qtd_inicial,
               IFNULL(SUM(iv.quantidade), 0) AS vendidos
        FROM produtos p
        LEFT JOIN itens_venda iv ON p.id = iv.produto_id
        WHERE p.usuario_id = %s
        GROUP BY p.id
    """, (session['usuario_id'],))
    produtos = cursor.fetchall()
    for p in produtos:
        p['em_estoque'] = p['qtd_inicial'] - p['vendidos']
    return render_template('estoque.html', produtos=produtos)

@main_bp.route('/ver_previsao')
@login_required
def ver_previsao():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.id, p.nome, iv.quantidade, v.data
        FROM itens_venda iv
        JOIN vendas v ON iv.venda_id = v.id
        JOIN produtos p ON iv.produto_id = p.id
        WHERE v.usuario_id = %s
    """, (session['usuario_id'],))
    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    if not dados:
        return render_template("ver_previsao.html", grafico="<p>Sem dados suficientes para prever.</p>")

    df = pd.DataFrame(dados)
    df['data'] = pd.to_datetime(df['data'])

    os.makedirs("tcc_app/static/previsao", exist_ok=True)
    caminho = "tcc_app/static/previsao/previsao.png"

    fig, ax = plt.subplots(figsize=(10, 6))
    produtos = df['nome'].unique()

    for produto in produtos:
        df_prod = df[df['nome'] == produto]
        df_grouped = df_prod.groupby('data').sum().reset_index()
        df_grouped['dias'] = (df_grouped['data'] - df_grouped['data'].min()).dt.days

        if len(df_grouped) >= 2:
            modelo = LinearRegression()
            modelo.fit(df_grouped[['dias']], df_grouped['quantidade'])

            dias_futuros = list(range(df_grouped['dias'].max() + 1, df_grouped['dias'].max() + 8))
            datas_futuras = [df_grouped['data'].min() + timedelta(days=int(d)) for d in dias_futuros]
            previsoes = modelo.predict(pd.DataFrame({'dias': dias_futuros}))

            ax.plot(df_grouped['data'], df_grouped['quantidade'], label=f"{produto} (real)")
            ax.plot(datas_futuras, previsoes, '--', label=f"{produto} (previsão)")

    ax.set_title("Previsão de Vendas por Produto")
    ax.set_xlabel("Data")
    ax.set_ylabel("Quantidade")
    ax.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(caminho)
    plt.close()

    return render_template("ver_previsao.html", grafico=f"<img src='/static/previsao/previsao.png'>")

@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.id, p.nome, p.quantidade AS qtd_inicial,
            COALESCE(SUM(iv.quantidade), 0) AS qtd_vendida,
            COALESCE(SUM(iv.quantidade * p.preco_custo), 0) AS custo_total,
            COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0) AS receita_total
        FROM produtos p
        LEFT JOIN itens_venda iv ON iv.produto_id = p.id
        LEFT JOIN vendas v ON iv.venda_id = v.id AND v.usuario_id = %s
        WHERE p.usuario_id = %s
        GROUP BY p.id
    """, (session['usuario_id'], session['usuario_id']))
    produtos = cursor.fetchall()

    cursor.close()
    conn.close()

    nomes = [p['nome'] for p in produtos]
    vendidos = [p['qtd_vendida'] for p in produtos]
    em_estoque = [p['qtd_inicial'] - p['qtd_vendida'] for p in produtos]
    custo = [p['custo_total'] for p in produtos]
    lucro = [p['receita_total'] - p['custo_total'] for p in produtos]

    return render_template("dashboard.html", nomes=nomes, vendidos=vendidos, em_estoque=em_estoque, custo=custo, lucro=lucro)
