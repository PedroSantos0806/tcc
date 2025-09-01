from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, abort
from tcc_app.db import get_db_connection
import csv, os

main_bp = Blueprint('main_bp', __name__)

# ===================== CSV helpers =====================
def _csv_path(name):
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'data', name)

def _read_csv(name):
    path = _csv_path(name)
    if not os.path.exists(path): return []
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))

def _csv_user_id_for_email(email):
    for row in _read_csv('users.csv'):
        if (row.get('email','') or '').strip().lower() == (email or '').lower():
            try:
                return int(row.get('id') or 0)
            except:
                return None
    return None

def _csv_categories_for_email(email):
    """ Retorna lista de categorias distintas do CSV para o usuário (por e-mail). """
    uid = _csv_user_id_for_email(email)
    if not uid:
        return []
    products = [p for p in _read_csv('products.csv') if p.get('usuario_id') == str(uid)]
    cats = sorted({ (p.get('categoria') or '').strip() for p in products if (p.get('categoria') or '').strip() })
    return cats

def _csv_dashboard_rows(uid_db, email, categoria_sel=None):
    """
    Monta métricas por produto a partir do CSV:
    retorna cada item como: {"nome","qtd_vendida","qtd_inicial","custo_total","receita_total"}
    Respeita categoria_sel quando informado.
    """
    u_csv_id = _csv_user_id_for_email(email)
    if not u_csv_id: return []

    products_all = [p for p in _read_csv('products.csv') if p.get('usuario_id') == str(u_csv_id)]
    if categoria_sel:
        products = [p for p in products_all if (p.get('categoria') or '').strip() == categoria_sel]
    else:
        products = products_all
    prod_ids = {p['id'] for p in products}

    sales    = [s for s in _read_csv('sales.csv') if s.get('usuario_id') == str(u_csv_id)]
    items    = _read_csv('items.csv')

    sale_ids = {s['id'] for s in sales}
    items    = [i for i in items if i.get('venda_id') in sale_ids and i.get('produto_id') in prod_ids]

    # agregação por produto
    agg = {}
    for p in products:
        agg[p['id']] = {
            "nome": p['nome'],
            "qtd_inicial": int(p.get('quantidade') or 0),
            "preco_custo": float(p.get('preco_custo') or 0),
            "preco_venda": float(p.get('preco_venda') or 0),
            "vendidos": 0,
            "custo_total": 0.0,
            "receita_total": 0.0
        }
    for it in items:
        pid = it.get('produto_id')
        if pid in agg:
            q = int(it.get('quantidade') or 0)
            pu = float(it.get('preco_unitario') or 0)
            agg[pid]["vendidos"] += q
            agg[pid]["receita_total"] += q * pu
            agg[pid]["custo_total"]   += q * agg[pid]["preco_custo"]

    out = []
    for p in agg.values():
        out.append({
            "nome": p["nome"],
            "qtd_vendida": p["vendidos"],
            "qtd_inicial": p["qtd_inicial"],
            "custo_total": p["custo_total"],
            "receita_total": p["receita_total"]
        })
    return out

def _csv_previsao_series(email, categoria_sel=None):
    """
    Retorna dict por dia {'YYYY-MM-DD': total_qtd} vindo do CSV,
    filtrando por categoria quando informado.
    """
    u_csv_id = _csv_user_id_for_email(email)
    if not u_csv_id: return {}
    products = [p for p in _read_csv('products.csv') if p.get('usuario_id') == str(u_csv_id)]
    if categoria_sel:
        products = [p for p in products if (p.get('categoria') or '').strip() == categoria_sel]
    prod_ids = {p['id'] for p in products}

    sales = [s for s in _read_csv('sales.csv') if s.get('usuario_id') == str(u_csv_id)]
    sale_id_by_date = {s['id']: (s.get('data') or '').split('T')[0] for s in sales}

    items = [i for i in _read_csv('items.csv') if i.get('produto_id') in prod_ids and i.get('venda_id') in sale_id_by_date]

    from collections import defaultdict
    daily = defaultdict(int)
    for it in items:
        dia = sale_id_by_date[it['venda_id']]
        try:
            q = int(it.get('quantidade') or 0)
        except: 
            q = 0
        daily[dia] += q
    return dict(daily)

# ===================== Rotas =====================
@main_bp.route('/')
def home():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    return render_template('home.html', nome=session.get('usuario_nome'))

# =============== CADASTRAR PRODUTO ===============
@main_bp.route('/cadastrar_produto', methods=['GET', 'POST'])
def cadastrar_produto():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        f = request.form
        obrig = ['nome', 'preco_custo', 'preco_venda', 'quantidade', 'categoria', 'data_chegada']
        if any(not f.get(k) for k in obrig):
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_produto'))
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # 'preco' (base) pode não existir no schema antigo; aqui preenche com preco_custo por compatibilidade
            preco_base = f.get('preco') or f.get('preco_custo')
            cur.execute("""
                INSERT INTO produtos (nome,preco,preco_custo,preco_venda,quantidade,categoria,subcategoria,tamanho,data_chegada,usuario_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                f['nome'], preco_base, f['preco_custo'], f['preco_venda'], f['quantidade'],
                f['categoria'], f.get('subcategoria') or None, f.get('tamanho') or None,
                f['data_chegada'], session['usuario_id']
            ))
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
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
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
                if not pid or not q:
                    continue
                cur.execute("SELECT preco_venda FROM produtos WHERE id=%s AND usuario_id=%s", (pid, uid))
                row = cur.fetchone()
                if not row:
                    continue
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
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip() or None

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id=%s", (uid,))
    categorias = sorted([r['categoria'] for r in cur.fetchall() if r['categoria']])

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

    tabela, total_itens, total_custo, total_venda = [], 0, 0.0, 0.0
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
    return render_template(
        'ver_estoque.html',
        produtos=tabela,
        categorias=categorias,
        categoria_selecionada=categoria_sel,
        kpis=kpis
    )

# =============== DASHBOARD (PÁGINA) ===============
@main_bp.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    email = session.get('usuario_email')

    # categorias do DB
    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id=%s", (uid,))
    categorias_db = [r['categoria'] for r in cur.fetchall() if r['categoria']]
    cur.close(); conn.close()

    # categorias do CSV (se houver)
    categorias_csv = _csv_categories_for_email(email)

    # merge + ordena
    categorias = sorted({*categorias_db, *categorias_csv})

    categoria_sel = request.args.get('categoria', '').strip()
    return render_template(
        "dashboard.html",
        categorias=categorias,
        categoria_selecionada=categoria_sel,
        nomes=[], vendidos=[], em_estoque=[], custo=[], lucro=[]
    )

# =============== DASHBOARD (API JSON) ===============
@main_bp.route('/api/dashboard')
def api_dashboard():
    if 'usuario_id' not in session:
        return jsonify({})
    uid = session['usuario_id']
    email = session.get('usuario_email')
    categoria_sel = request.args.get('categoria', '').strip() or None

    # DB
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
    db_rows = cur.fetchall()
    cur.close(); conn.close()

    # CSV (com filtro de categoria aplicado)
    csv_rows = _csv_dashboard_rows(uid, email, categoria_sel=categoria_sel)

    # Mesclar por nome (soma os valores)
    from collections import defaultdict
    agg = defaultdict(lambda: {"vendidos":0,"estoque":0,"custo":0.0,"lucro":0.0})
    def add_row(nome, qtd_inicial, qtd_vendida, custo_total, receita_total):
        agg[nome]["vendidos"] += int(qtd_vendida or 0)
        est = max(0, int(qtd_inicial or 0) - int(qtd_vendida or 0))
        agg[nome]["estoque"] += est
        agg[nome]["custo"]   += float(custo_total or 0.0)
        agg[nome]["lucro"]   += float((receita_total or 0.0) - (custo_total or 0.0))

    for r in db_rows:
        add_row(r['nome'], r['qtd_inicial'], r['qtd_vendida'], r['custo_total'], r['receita_total'])
    for r in csv_rows:
        add_row(r['nome'], r['qtd_inicial'], r['qtd_vendida'], r['custo_total'], r['receita_total'])

    labels = list(agg.keys())
    vendidos = [agg[n]["vendidos"] for n in labels]
    estoque  = [agg[n]["estoque"]  for n in labels]
    custo    = [round(agg[n]["custo"],2) for n in labels]
    lucro    = [round(agg[n]["lucro"],2) for n in labels]
    return jsonify({"labels": labels, "vendidos": vendidos, "estoque": estoque, "custo": custo, "lucro": lucro})

# =============== PREVISÃO (PÁGINA) ===============
@main_bp.route('/ver_previsao')
def ver_previsao():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    email = session.get('usuario_email')

    # categorias do DB
    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id=%s", (uid,))
    categorias_db = [r['categoria'] for r in cur.fetchall() if r['categoria']]
    cur.close(); conn.close()

    # categorias do CSV
    categorias_csv = _csv_categories_for_email(email)

    categorias = sorted({*categorias_db, *categorias_csv})
    categoria_sel = request.args.get('categoria', '').strip()
    return render_template("ver_previsao.html", grafico=None, categorias=categorias, categoria_selecionada=categoria_sel)

# =============== PREVISÃO (API JSON) ===============
@main_bp.route('/api/previsao')
def api_previsao():
    if 'usuario_id' not in session:
        return jsonify({})
    uid = session['usuario_id']
    email = session.get('usuario_email')
    categoria_sel = request.args.get('categoria', '').strip() or None

    # Série do DB: soma quantidade por dia
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

    # Série do CSV (por e-mail), com filtro de categoria
    csv_daily = _csv_previsao_series(email, categoria_sel)

    # Mescla DB + CSV por dia
    from collections import defaultdict
    daily = defaultdict(int)
    for r in rows:
        daily[str(r['dia'])] += int(r['qtd'] or 0)
    for k, v in (csv_daily or {}).items():
        daily[k] += int(v or 0)

    if not daily:
        return jsonify({"labels_hist": [], "hist": [], "labels_pred": [], "pred": []})

    # ===== Modelo leve: tendência + sazonalidade semanal + média móvel (MM7) =====
    import numpy as np, datetime as _dt
    days_sorted = sorted(daily.keys())
    y = np.array([daily[d] for d in days_sorted], dtype=float)
    n = len(y)
    t = np.arange(n, dtype=float)

    # tendência linear
    if n >= 2:
        a, b = np.polyfit(t, y, 1)
        trend = a * t + b
    else:
        trend = np.full(n, y.mean() if n else 0.0)

    # sazonalidade semanal (resíduos médios por dia da semana)
    dow_means = {i: [] for i in range(7)}
    for i, d in enumerate(days_sorted):
        dt_obj = _dt.date.fromisoformat(d)
        dow_means[dt_obj.weekday()].append(y[i] - trend[i])
    dow_adj = {k: (np.mean(v) if v else 0.0) for k, v in dow_means.items()}

    # previsão 14 dias
    h = 14
    future_days = []
    future_y = []
    last_day = _dt.date.fromisoformat(days_sorted[-1])
    mm7 = y[-7:].mean() if n >= 1 else 0.0
    for i in range(1, h + 1):
        fd = last_day + _dt.timedelta(days=i)
        tt = n - 1 + i
        base = (a * tt + b) if n >= 2 else (y.mean() if n else 0.0)
        seasonal = dow_adj[fd.weekday()]
        pred = 0.7 * (base + seasonal) + 0.3 * mm7
        if pred < 0: pred = 0.0
        future_days.append(fd.isoformat())
        future_y.append(round(float(pred), 2))

    return jsonify({
        "labels_hist": days_sorted[-60:],
        "hist": [float(v) for v in y.tolist()][-60:],
        "labels_pred": future_days,
        "pred": future_y
    })

# =============== IMPORTAR CSV -> MYSQL (admin) ===============
@main_bp.route('/admin/import_csv', methods=['POST', 'GET'])
def import_csv():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    if session.get('usuario_email') != 'admin@demo.com':
        abort(403)

    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'data')
    users = os.path.join(base, 'users.csv')
    products = os.path.join(base, 'products.csv')
    sales = os.path.join(base, 'sales.csv')
    items = os.path.join(base, 'items.csv')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if os.path.exists(users):
            with open(users, encoding='utf-8') as f:
                r = csv.DictReader(f)
                for row in r:
                    cur.execute("""
                        REPLACE INTO usuarios (id, nome, email, senha)
                        VALUES (%s,%s,%s,%s)
                    """, (row['id'], row['nome'], row['email'], row['senha']))

        if os.path.exists(products):
            with open(products, encoding='utf-8') as f:
                r = csv.DictReader(f)
                for row in r:
                    cur.execute("""
                        REPLACE INTO produtos
                        (id, nome, preco, preco_custo, preco_venda, quantidade, categoria, subcategoria, tamanho, data_chegada, usuario_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        row['id'], row['nome'], row['preco'], row['preco_custo'], row['preco_venda'],
                        row['quantidade'], row['categoria'] or None, row['subcategoria'] or None,
                        row['tamanho'] or None, row['data_chegada'] or None, row['usuario_id']
                    ))

        if os.path.exists(sales):
            with open(sales, encoding='utf-8') as f:
                r = csv.DictReader(f)
                for row in r:
                    data = row['data'].replace('T',' ').split('.')[0]
                    cur.execute("""
                        REPLACE INTO vendas (id, usuario_id, data)
                        VALUES (%s,%s,%s)
                    """, (row['id'], row['usuario_id'], data))

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
