from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from tcc_app.utils import login_required, MEM, get_produto, add_produto, add_venda, add_item_venda, get_usuario
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

# ----------------------------
# CADASTRAR PRODUTO (MEMÓRIA)
# ----------------------------
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

        if (not nome or not preco or not preco_custo or not preco_venda or
            quantidade is None or not categoria or not data_chegada):
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_produto'))

        try:
            novo = {
                "nome": nome,
                "preco": float(preco),
                "preco_custo": float(preco_custo),
                "preco_venda": float(preco_venda),
                "quantidade": int(quantidade),
                "categoria": categoria,
                "subcategoria": subcategoria or "",
                "tamanho": tamanho or "",
                "data_chegada": data_chegada,
                "usuario_id": session['usuario_id']
            }
            add_produto(novo)
            flash('Produto cadastrado com sucesso!')
        except Exception as e:
            print("Erro ao cadastrar produto:", e)
            flash('Erro ao cadastrar produto.')

        return redirect(url_for('main_bp.cadastrar_produto'))

    return render_template('cadastrar_produto.html')

# ----------------------------
# CADASTRAR VENDA (MEMÓRIA)
# ----------------------------
@main_bp.route('/cadastrar_venda', methods=['GET', 'POST'])
@login_required
def cadastrar_venda():
    usuario_id = session['usuario_id']
    # Produtos do usuário logado
    produtos = [p for p in MEM["produtos"] if p["usuario_id"] == usuario_id]

    if request.method == 'POST':
        data_venda = request.form.get('data_venda')
        produto_ids = request.form.getlist('produto_id[]')
        quantidades = request.form.getlist('quantidade[]')

        if not data_venda or not produto_ids or not quantidades:
            flash("Preencha todos os campos.")
            return redirect(url_for('main_bp.cadastrar_venda'))

        try:
            v = add_venda(usuario_id, data_venda)
            for produto_id, qtd in zip(produto_ids, quantidades):
                if not produto_id or not qtd:
                    continue
                p = get_produto(int(produto_id))
                if not p:
                    continue
                add_item_venda(v["id"], p["id"], int(qtd), p["preco_venda"])
            flash("Venda registrada com sucesso!")
        except Exception as e:
            print("Erro ao registrar venda:", e)
            flash("Erro ao registrar venda.")

        return redirect(url_for('main_bp.cadastrar_venda'))

    return render_template("registrar_venda.html", produtos=produtos)

# ----------------------------
# ESTOQUE (MEMÓRIA)
# ----------------------------
@main_bp.route('/ver_estoque')
@login_required
def ver_estoque():
    usuario_id = session['usuario_id']
    produtos = [p for p in MEM["produtos"] if p["usuario_id"] == usuario_id]

    # Calcula vendidos por produto
    vendidos_por_prod = {}
    for item in MEM["itens_venda"]:
        venda = next((v for v in MEM["vendas"] if v["id"] == item["venda_id"]), None)
        if not venda or venda["usuario_id"] != usuario_id:
            continue
        vendidos_por_prod[item["produto_id"]] = vendidos_por_prod.get(item["produto_id"], 0) + item["quantidade"]

    # Monta tabela
    tabela = []
    for p in produtos:
        vendidos = vendidos_por_prod.get(p["id"], 0)
        tabela.append({
            "id": p["id"], "nome": p["nome"],
            "categoria": p["categoria"], "subcategoria": p["subcategoria"], "tamanho": p["tamanho"],
            "preco": p["preco"], "qtd_inicial": p["quantidade"], "vendidos": vendidos,
            "quantidade_atual": p["quantidade"] - vendidos
        })
    return render_template('ver_estoque.html', produtos=tabela)

# ----------------------------
# PREVISÃO (MEMÓRIA)
# ----------------------------
@main_bp.route('/ver_previsao')
@login_required
def ver_previsao():
    usuario_id = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip()

    # Junta itens + vendas + produtos (do usuário)
    rows = []
    for item in MEM["itens_venda"]:
        venda = next((v for v in MEM["vendas"] if v["id"] == item["venda_id"]), None)
        prod = get_produto(item["produto_id"])
        if not venda or not prod:
            continue
        if venda["usuario_id"] != usuario_id:
            continue
        if categoria_sel and prod["categoria"] != categoria_sel:
            continue
        rows.append({
            "produto_id": prod["id"],
            "nome": prod["nome"],
            "quantidade": item["quantidade"],
            "data": venda["data"]
        })

    categorias = sorted(set([p["categoria"] for p in MEM["produtos"] if p["usuario_id"] == usuario_id]))
    if not rows:
        return render_template("ver_previsao.html",
                               grafico="<p>Sem dados suficientes para prever.</p>",
                               categorias=categorias, categoria_selecionada=categoria_sel)

    df = pd.DataFrame(rows)
    df['data'] = pd.to_datetime(df['data'])

    os.makedirs("tcc_app/static/previsao", exist_ok=True)
    caminho = "tcc_app/static/previsao/previsao.png"

    fig, ax = plt.subplots(figsize=(10, 6))
    for produto in df['nome'].unique():
        df_prod = df[df['nome'] == produto].copy()
        df_grouped = df_prod.groupby('data', as_index=False)['quantidade'].sum()
        df_grouped = df_grouped.sort_values('data')
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

    return render_template("ver_previsao.html",
                           grafico=f"<img src='/static/previsao/previsao.png'>",
                           categorias=categorias, categoria_selecionada=categoria_sel)

# ----------------------------
# DASHBOARD (MEMÓRIA)
# ----------------------------
@main_bp.route('/dashboard')
@login_required
def dashboard():
    usuario_id = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip()

    # Produtos do usuário (com filtro opcional de categoria)
    produtos_user = [p for p in MEM["produtos"] if p["usuario_id"] == usuario_id]
    categorias = sorted(set([p["categoria"] for p in produtos_user]))
    if categoria_sel:
        produtos_user = [p for p in produtos_user if p["categoria"] == categoria_sel]

    # Vendas agregadas por produto
    vendidos_por_prod = {}
    receita_por_prod = {}
    custo_por_prod = {}
    for item in MEM["itens_venda"]:
        venda = next((v for v in MEM["vendas"] if v["id"] == item["venda_id"]), None)
        prod = get_produto(item["produto_id"])
        if not venda or not prod:
            continue
        if venda["usuario_id"] != usuario_id:
            continue
        if categoria_sel and prod["categoria"] != categoria_sel:
            continue
        pid = prod["id"]
        vendidos_por_prod[pid] = vendidos_por_prod.get(pid, 0) + item["quantidade"]
        receita_por_prod[pid] = receita_por_prod.get(pid, 0) + item["quantidade"] * item["preco_unitario"]
        custo_por_prod[pid] = custo_por_prod.get(pid, 0) + item["quantidade"] * float(prod["preco_custo"])

    nomes, vendidos, em_estoque, custo, lucro = [], [], [], [], []
    for p in produtos_user:
        pid = p["id"]
        qvend = vendidos_por_prod.get(pid, 0)
        nomes.append(p["nome"])
        vendidos.append(qvend)
        em_estoque.append(max(0, int(p["quantidade"]) - int(qvend)))
        ct = round(custo_por_prod.get(pid, 0.0), 2)
        rc = round(receita_por_prod.get(pid, 0.0), 2)
        custo.append(ct)
        lucro.append(round(rc - ct, 2))

    return render_template("dashboard.html",
                           nomes=nomes, vendidos=vendidos, em_estoque=em_estoque,
                           custo=custo, lucro=lucro,
                           categorias=categorias, categoria_selecionada=categoria_sel)
