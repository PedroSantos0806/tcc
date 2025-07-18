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

@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    categoria = request.args.get('categoria')
    filtro_categoria = ""
    params = [session['usuario_id'], session['usuario_id']]
    if categoria:
        filtro_categoria = " AND p.categoria = %s"
        params.append(categoria)

    cursor.execute(f"""
        SELECT p.id, p.nome, p.quantidade AS qtd_inicial,
            COALESCE(SUM(iv.quantidade), 0) AS qtd_vendida,
            COALESCE(SUM(iv.quantidade * p.preco_custo), 0) AS custo_total,
            COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0) AS receita_total
        FROM produtos p
        LEFT JOIN itens_venda iv ON iv.produto_id = p.id
        LEFT JOIN vendas v ON iv.venda_id = v.id AND v.usuario_id = %s
        WHERE p.usuario_id = %s {filtro_categoria}
        GROUP BY p.id
    """, tuple(params))

    produtos = cursor.fetchall()

    cursor.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id = %s", (session['usuario_id'],))
    categorias = [row['categoria'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    nomes = [p['nome'] for p in produtos]
    vendidos = [p['qtd_vendida'] for p in produtos]
    em_estoque = [p['qtd_inicial'] - p['qtd_vendida'] for p in produtos]
    custo = [float(p['custo_total']) for p in produtos]
    lucro = [float(p['receita_total']) - float(p['custo_total']) for p in produtos]

    return render_template("dashboard.html",
        nomes=nomes,
        vendidos=vendidos,
        em_estoque=em_estoque,
        custo=custo,
        lucro=lucro,
        categorias=categorias,
        categoria_selecionada=categoria
    )

@main_bp.route('/ver_previsao')
@login_required
def ver_previsao():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    categoria = request.args.get('categoria')
    query = """
        SELECT p.id, p.nome, iv.quantidade, v.data, p.categoria
        FROM itens_venda iv
        JOIN vendas v ON iv.venda_id = v.id
        JOIN produtos p ON iv.produto_id = p.id
        WHERE v.usuario_id = %s
    """
    params = [session['usuario_id']]
    if categoria:
        query += " AND p.categoria = %s"
        params.append(categoria)

    cursor.execute(query, params)
    dados = cursor.fetchall()

    cursor.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id = %s", (session['usuario_id'],))
    categorias = [row['categoria'] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    if not dados:
        return render_template("ver_previsao.html", grafico=None, categorias=categorias, categoria_selecionada=categoria)

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

    return render_template("ver_previsao.html", grafico=f"<img src='/static/previsao/previsao.png'>", categorias=categorias, categoria_selecionada=categoria)
