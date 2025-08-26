from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, abort
from tcc_app.db import get_db_connection
import csv, os
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def home():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    return render_template('home.html', nome=session.get('usuario_nome'))

# =============== CADASTRAR PRODUTO ===============
@main_bp.route('/cadastrar_produto', methods=['GET', 'POST'])
def cadastrar_produto():
    if 'usuario_id' not in session: return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        f = request.form
        obrig = ['nome','preco','preco_custo','preco_venda','quantidade','categoria','data_chegada']
        if any(not f.get(k) for k in obrig):
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_produto'))
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO produtos (nome,preco,preco_custo,preco_venda,quantidade,categoria,subcategoria,tamanho,data_chegada,usuario_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (f['nome'], f['preco'], f['preco_custo'], f['preco_venda'], f['quantidade'],
                  f['categoria'], f.get('subcategoria') or None, f.get('tamanho') or None,
                  f['data_chegada'], session['usuario_id']))
            conn.commit()
            cur.close(); conn.close()
            flash('Produto cadastrado com sucesso!')
        except Exception as e:
            print("Erro ao cadastrar produto:", e)
            flash('Erro ao cadastrar produto.')
        return redirect(url_for('main_bp.cadastrar_produto'))
    return render_template('cadastrar_produto.html')

# =============== CADASTRAR VENDA ===============
@main_bp.route('/cadastrar_venda', methods=['GET', 'POST'])
def cadastrar_venda():
    if 'usuario_id' not in session: return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM produtos WHERE usuario_id=%s ORDER BY nome", (uid,))
    produtos = cur.fetchall()

    if request.method == 'POST':
        data_venda = request.form.get('data_venda')
        ids = request.form.getlist('produto_id[]')
        qtds = request.form.getlist('quantidade[]')
        if not data_venda or not ids or not qtds:
            flash("Preencha todos os campos.")
            cur.close(); conn.close()
            return redirect(url_for('main_bp.cadastrar_venda'))
        try:
            cur.execute("INSERT INTO vendas (usuario_id, data) VALUES (%s, %s)", (uid, data_venda))
            venda_id = cur.lastrowid
            for pid, q in zip(ids, qtds):
                if not pid or not q: continue
                cur.execute("SELECT preco_venda FROM produtos WHERE id=%s AND usuario_id=%s", (pid, uid))
                row = cur.fetchone()
                if not row: continue
                cur.execute("""
                    INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
                    VALUES (%s,%s,%s,%s)
                """, (venda_id, pid, int(q), float(row['preco_venda'])))
            conn.commit()
            flash("Venda registrada com sucesso!")
        except Exception as e:
            print("Erro ao registrar venda:", e)
            conn.rollback()
            flash("Erro ao registrar venda.")
        cur.close(); conn.close()
        return redirect(url_for('main_bp.cadastrar_venda'))

    cur.close(); conn.close()
    return render_template("registrar_venda.html", produtos=produtos)

# =============== ESTOQUE (PÁGINA) ===============
@main_bp.route('/ver_estoque')
def ver_estoque():
    if 'usuario_id' not in session: return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip() or None

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # categorias disponíveis
    cur.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id=%s", (uid,))
    categorias = sorted([r['categoria'] for r in cur.fetchall() if r['categoria']])

    # tabela
    sql = """
    SELECT p.id, p.nome, p.categoria, p.preco_venda, p.preco_custo, p.quantidade AS qtd_inicial,
           COALESCE(SUM(iv.quantidade),0) AS vendidos
    FROM produtos p
    LEFT JOIN itens_venda iv ON iv.produto_id = p.id
    LEFT JOIN vendas v ON v.id = iv.venda_id AND v.usuario_id = %s
    WHERE p.usuario_id = %s
    """
    params = [uid, uid]
    if categoria_sel:
        sql += " AND p.categoria = %s"
        params.append(categoria_sel)
    sql += " GROUP BY p.id ORDER BY (p.quantidade - COALESCE(SUM(iv.quantidade),0)) ASC"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()

    tabela = []
    total_itens = 0
    total_custo = 0.0
    total_venda = 0.0
    for r in rows:
        em_estoque = int(r['qtd_inicial']) - int(r['vendidos'])
        if em_estoque < 0: em_estoque = 0
        total_itens += em_estoque
        total_custo += em_estoque * float(r['preco_custo'])
        total_venda += em_estoque * float(r['preco_venda'])
        perc_vendido = 0.0
        if int(r['qtd_inicial']) > 0:
            perc_vendido = round(100.0 * int(r['vendidos']) / int(r['qtd_inicial']), 1)
        baixo_limite = max(5, int(0.2 * int(r['qtd_inicial'])))
        status = "Baixo" if em_estoque <= baixo_limite else "OK"

        tabela.append({
            "id": r['id'],
            "nome": r['nome'],
            "categoria": r['categoria'],
            "preco_venda": float(r['preco_venda']),
            "preco_custo": float(r['preco_custo']),
            "qtd_inicial": int(r['qtd_inicial']),
            "vendidos": int(r['vendidos']),
            "em_estoque": int(em_estoque),
            "perc_vendido": perc_vendido,
            "status": status
        })

    kpis = {
        "produtos": len(tabela),
        "itens": int(total_itens),
        "valor_custo": round(total_custo, 2),
        "valor_venda": round(total_venda, 2)
    }
    return render_template('ver_estoque.html',
                           produtos=tabela,
                           categorias=categorias,
                           categoria_selecionada=categoria_sel,
                           kpis=kpis)

# =============== DASHBOARD (PÁGINA) ===============
@main_bp.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session: return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id=%s", (uid,))
    categorias = sorted([r['categoria'] for r in cur.fetchall() if r['categoria']])
    cur.close(); conn.close()
    categoria_sel = request.args.get('categoria', '').strip()
    return render_template("dashboard.html", categorias=categorias, categoria_selecionada=categoria_sel,
                           nomes=[], vendidos=[], em_estoque=[], custo=[], lucro=[])

# =============== DASHBOARD (API JSON) ===============
@main_bp.route('/api/dashboard')
def api_dashboard():
    if 'usuario_id' not in session: return jsonify({})
    uid = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip() or None

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    sql = """
    SELECT p.id, p.nome, p.quantidade AS qtd_inicial, p.preco_custo, p.preco_venda,
           COALESCE(SUM(iv.quantidade),0) AS qtd_vendida,
           COALESCE(SUM(iv.quantidade * iv.preco_unitario),0) AS receita_total,
           COALESCE(SUM(iv.quantidade * p.preco_custo),0) AS custo_total
    FROM produtos p
    LEFT JOIN itens_venda iv ON iv.produto_id = p.id
    LEFT JOIN vendas v ON v.id = iv.venda_id AND v.usuario_id = %s
    WHERE p.usuario_id = %s
    """
    params = [uid, uid]
    if categoria_sel:
        sql += " AND p.categoria = %s"
        params.append(categoria_sel)
    sql += " GROUP BY p.id ORDER BY p.nome"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()

    labels = [r['nome'] for r in rows]
    vendidos = [int(r['qtd_vendida']) for r in rows]
    em_estoque = [max(0, int(r['qtd_inicial']) - int(r['qtd_vendida'])) for r in rows]
    custo = [float(r['custo_total']) for r in rows]
    lucro = [float(r['receita_total']) - float(r['custo_total']) for r in rows]
    return jsonify({"labels": labels, "vendidos": vendidos, "estoque": em_estoque, "custo": custo, "lucro": lucro})

# =============== PREVISÃO (PÁGINA) ===============
@main_bp.route('/ver_previsao')
def ver_previsao():
    if 'usuario_id' not in session: return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id=%s", (uid,))
    categorias = sorted([r['categoria'] for r in cur.fetchall() if r['categoria']])
    cur.close(); conn.close()
    categoria_sel = request.args.get('categoria', '').strip()
    return render_template("ver_previsao.html", grafico=None, categorias=categorias, categoria_selecionada=categoria_sel)

# =============== PREVISÃO (API JSON) ===============
@main_bp.route('/api/previsao')
def api_previsao():
    if 'usuario_id' not in session: return jsonify({})
    uid = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip() or None

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    sql = """
    SELECT DATE(v.data) AS dia, SUM(iv.quantidade) AS qtd
    FROM vendas v
    JOIN itens_venda iv ON iv.venda_id = v.id
    JOIN produtos p ON p.id = iv.produto_id
    WHERE v.usuario_id = %s
    """
    params = [uid]
    if categoria_sel:
        sql += " AND p.categoria = %s"
        params.append(categoria_sel)
    sql += " GROUP BY DATE(v.data) ORDER BY dia"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()

    if not rows:
        return jsonify({"labels_hist": [], "hist": [], "labels_pred": [], "pred": []})

    s = pd.Series({r['dia']: int(r['qtd']) for r in rows}).sort_index()
    s.index = pd.to_datetime(s.index)

    # Features: tendência + dummies dow
    X = pd.DataFrame({"t": np.arange(len(s)), "dow": s.index.dayofweek}, index=s.index)
    X = pd.get_dummies(X, columns=["dow"], drop_first=True)
    y = s.values
    model = Ridge(alpha=1.0).fit(X, y)

    h = 14
    fut_idx = pd.date_range(s.index.max() + pd.Timedelta(days=1), periods=h, freq="D")
    Xf = pd.DataFrame({"t": np.arange(len(s), len(s)+h), "dow": fut_idx.dayofweek}, index=fut_idx)
    Xf = pd.get_dummies(Xf, columns=["dow"], drop_first=True).reindex(columns=X.columns, fill_value=0)
    y_lr = model.predict(Xf)

    ma7 = s.rolling(7, min_periods=1).mean().iloc[-1]
    y_pred = np.clip(0.7*y_lr + 0.3*ma7, 0, None)

    return jsonify({
        "labels_hist": s.index.strftime("%Y-%m-%d").tolist()[-60:],
        "hist": s.values.tolist()[-60:],
        "labels_pred": fut_idx.strftime("%Y-%m-%d").tolist(),
        "pred": y_pred.round(2).tolist()
    })

# =============== IMPORTAR CSV -> MYSQL (admin) ===============
@main_bp.route('/admin/import_csv', methods=['POST', 'GET'])
def import_csv():
    if 'usuario_id' not in session: return redirect(url_for('auth_bp.login'))
    # restringe ao admin por e-mail
    if session.get('usuario_email') != 'admin@demo.com':
        abort(403)

    base = os.path.join(os.path.dirname(__file__), 'instance', 'data')
    users = os.path.join(base, 'users.csv')
    products = os.path.join(base, 'products.csv')
    sales = os.path.join(base, 'sales.csv')
    items = os.path.join(base, 'items.csv')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # USUÁRIOS
        if os.path.exists(users):
            with open(users, encoding='utf-8') as f:
                r = csv.DictReader(f)
                for row in r:
                    cur.execute("""
                        REPLACE INTO usuarios (id, nome, email, senha)
                        VALUES (%s,%s,%s,%s)
                    """, (row['id'], row['nome'], row['email'], row['senha']))

        # PRODUTOS
        if os.path.exists(products):
            with open(products, encoding='utf-8') as f:
                r = csv.DictReader(f)
                for row in r:
                    cur.execute("""
                        REPLACE INTO produtos
                        (id, nome, preco, preco_custo, preco_venda, quantidade, categoria, subcategoria, tamanho, data_chegada, usuario_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (row['id'], row['nome'], row['preco'], row['preco_custo'], row['preco_venda'],
                          row['quantidade'], row['categoria'] or None, row['subcategoria'] or None,
                          row['tamanho'] or None, row['data_chegada'] or None, row['usuario_id']))

        # VENDAS
        if os.path.exists(sales):
            with open(sales, encoding='utf-8') as f:
                r = csv.DictReader(f)
                for row in r:
                    data = row['data'].replace('T',' ').split('.')[0]
                    cur.execute("""
                        REPLACE INTO vendas (id, usuario_id, data)
                        VALUES (%s,%s,%s)
                    """, (row['id'], row['usuario_id'], data))

        # ITENS
        if os.path.exists(items):
            with open(items, encoding='utf-8') as f:
                r = csv.DictReader(f)
                for row in r:
                    cur.execute("""
                        REPLACE INTO itens_venda (id, venda_id, produto_id, quantidade, preco_unitario)
                        VALUES (%s,%s,%s,%s,%s)
                    """, (row['id'], row['venda_id'], row['produto_id'], row['quantidade'], row['preco_unitario']))

        conn.commit()
        cur.close(); conn.close()
        flash("Importação dos CSVs concluída!")
    except Exception as e:
        print("Erro ao importar CSV:", e)
        flash("Erro ao importar CSV. Veja os logs.")

    if request.method == 'POST':
        return redirect(url_for('main_bp.home'))
    return render_template('admin_import.html')
