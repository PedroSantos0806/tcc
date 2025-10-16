from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, abort
from tcc_app.db import get_db_connection
import csv, os, datetime as dt

main_bp = Blueprint('main_bp', __name__)

# ===================== i18n (leve) =====================
I18N = {
    "pt": {
        "Dashboard": "Dashboard",
        "Menu": "Menu",
        "Stock": "Estoque",
        "Shopping List": "Lista de Compras",
        "Reports": "Relatórios",
        "Logout": "Sair",
        "Sign in": "Entrar",
        "Email": "E-mail",
        "Password": "Senha",
        "Remember me": "Lembrar de mim",
        "Forgot password?": "Esqueceu a senha?",
        "Create free account": "Criar conta gratuita",
        "Or": "ou",
        "Start now": "Começar agora",
        "See demo": "Ver demo",
        "Real demand forecasting": "Previsão de Demanda de verdade",
        "Login subtitle": "Acesse sua conta para gerenciar estoque, vendas e previsões com IA.",
        "Trusted line": "Relatórios, Estoque e Previsão com IA",
        "Onboarding Title": "Conte sobre o seu negócio",
        "Onboarding Subtitle": "Personalizamos o PrevFood conforme seu segmento.",
        "Business Type": "Tipo de estabelecimento",
        "Restaurant": "Restaurante / Lanchonete",
        "Retail": "Varejo (moda, calçados, etc.)",
        "Bakery": "Padaria / Confeitaria",
        "Pharmacy": "Farmácia",
        "Market": "Mercado / Mercearia",
        "Other": "Outro",
        "Preferred Language": "Idioma preferido",
        "Portuguese": "Português (Brasil)",
        "English": "Inglês",
        "Spanish": "Espanhol",
        "Save and continue": "Salvar e continuar",
        "Profile saved": "Preferências salvas!",
        "Name": "Nome",
        "Sign up": "Criar conta",
        "Have account?": "Já tem conta?",
        "Sign in now": "Entrar agora",
    },
    "en": {
        "Dashboard": "Dashboard",
        "Menu": "Menu",
        "Stock": "Stock",
        "Shopping List": "Shopping List",
        "Reports": "Reports",
        "Logout": "Logout",
        "Sign in": "Sign in",
        "Email": "Email",
        "Password": "Password",
        "Remember me": "Remember me",
        "Forgot password?": "Forgot password?",
        "Create free account": "Create free account",
        "Or": "or",
        "Start now": "Start now",
        "See demo": "See demo",
        "Real demand forecasting": "Real demand forecasting",
        "Login subtitle": "Access your account to manage inventory, sales and AI forecasts.",
        "Trusted line": "Reports, Inventory and AI Forecasting",
        "Onboarding Title": "Tell us about your business",
        "Onboarding Subtitle": "We personalize PrevFood by your segment.",
        "Business Type": "Business type",
        "Restaurant": "Restaurant / Diner",
        "Retail": "Retail (fashion, shoes, etc.)",
        "Bakery": "Bakery / Pastry",
        "Pharmacy": "Pharmacy",
        "Market": "Grocery / Market",
        "Other": "Other",
        "Preferred Language": "Preferred language",
        "Portuguese": "Portuguese (Brazil)",
        "English": "English",
        "Spanish": "Spanish",
        "Save and continue": "Save and continue",
        "Profile saved": "Preferences saved!",
        "Name": "Name",
        "Sign up": "Create account",
        "Have account?": "Already have an account?",
        "Sign in now": "Sign in now",
    },
    "es": {
        "Dashboard": "Panel",
        "Menu": "Menú",
        "Stock": "Inventario",
        "Shopping List": "Lista de Compras",
        "Reports": "Informes",
        "Logout": "Salir",
        "Sign in": "Iniciar sesión",
        "Email": "Correo",
        "Password": "Contraseña",
        "Remember me": "Recordarme",
        "Forgot password?": "¿Olvidó la contraseña?",
        "Create free account": "Crear cuenta gratis",
        "Or": "o",
        "Start now": "Empezar ahora",
        "See demo": "Ver demo",
        "Real demand forecasting": "Pronóstico de demanda real",
        "Login subtitle": "Accede para gestionar inventario, ventas y pronósticos con IA.",
        "Trusted line": "Informes, Inventario y Pronóstico con IA",
        "Onboarding Title": "Cuéntanos sobre tu negocio",
        "Onboarding Subtitle": "Personalizamos PrevFood según tu segmento.",
        "Business Type": "Tipo de negocio",
        "Restaurant": "Restaurante / Cafetería",
        "Retail": "Retail (moda, calzado, etc.)",
        "Bakery": "Panadería / Pastelería",
        "Pharmacy": "Farmacia",
        "Market": "Mercado / Tienda",
        "Other": "Otro",
        "Preferred Language": "Idioma preferido",
        "Portuguese": "Portugués (Brasil)",
        "English": "Inglés",
        "Spanish": "Español",
        "Save and continue": "Guardar y continuar",
        "Profile saved": "¡Preferencias guardadas!",
        "Name": "Nombre",
        "Sign up": "Crear cuenta",
        "Have account?": "¿Ya tienes cuenta?",
        "Sign in now": "Iniciar ahora",
    }
}

@main_bp.app_context_processor
def inject_i18n():
    lang = session.get('lang', 'pt')
    def t(key): return I18N.get(lang, I18N["pt"]).get(key, key)
    return dict(t=t, lang=lang)

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
            try: return int(row.get('id') or 0)
            except: return None
    return None

def _csv_categories_for_email(email):
    uid = _csv_user_id_for_email(email)
    if not uid: return []
    products = [p for p in _read_csv('products.csv') if p.get('usuario_id') == str(uid)]
    cats = sorted({ (p.get('categoria') or '').strip() for p in products if (p.get('categoria') or '').strip() })
    return cats

def _csv_dashboard_rows(uid_db, email, categoria_sel=None):
    u_csv_id = _csv_user_id_for_email(email)
    if not u_csv_id: return []
    products_all = [p for p in _read_csv('products.csv') if p.get('usuario_id') == str(u_csv_id)]
    products = [p for p in products_all if not categoria_sel or (p.get('categoria') or '').strip() == categoria_sel]
    prod_ids = {p['id'] for p in products}
    sales = [s for s in _read_csv('sales.csv') if s.get('usuario_id') == str(u_csv_id)]
    items = [i for i in _read_csv('items.csv') if i.get('venda_id') in {s['id'] for s in sales} and i.get('produto_id') in prod_ids]

    agg = {}
    for p in products:
        agg[p['id']] = {"nome": p['nome'], "qtd_inicial": int(p.get('quantidade') or 0),
                        "preco_custo": float(p.get('preco_custo') or 0),
                        "preco_venda": float(p.get('preco_venda') or 0),
                        "vendidos": 0, "custo_total": 0.0, "receita_total": 0.0}
    for it in items:
        pid = it.get('produto_id')
        if pid in agg:
            q = int(it.get('quantidade') or 0)
            pu = float(it.get('preco_unitario') or 0)
            agg[pid]["vendidos"] += q
            agg[pid]["receita_total"] += q * pu
            agg[pid]["custo_total"]   += q * agg[pid]["preco_custo"]

    return [{"nome": p["nome"], "qtd_vendida": p["vendidos"], "qtd_inicial": p["qtd_inicial"],
             "custo_total": p["custo_total"], "receita_total": p["receita_total"]} for p in agg.values()]

def _csv_previsao_series(email, categoria_sel=None):
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
        q = int(it.get('quantidade') or 0)
        daily[dia] += q
    return dict(daily)

# ===================== PÁGINAS PÚBLICAS =====================
@main_bp.route('/demo')
def demo():
    # Página pública de apresentação
    return render_template('demo.html')

# ===================== KPIs / Home =====================
def _kpis_semana(uid):
    hoje = dt.date.today()
    inicio = hoje - dt.timedelta(days=hoje.weekday())
    fim    = inicio + dt.timedelta(days=7)

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT COUNT(DISTINCT v.id) AS vendas,
               COALESCE(SUM(iv.quantidade * iv.preco_unitario),0) AS receita
        FROM vendas v
        LEFT JOIN itens_venda iv ON iv.venda_id = v.id
        WHERE v.usuario_id = %s AND v.data >= %s AND v.data < %s
    """, (uid, inicio, fim))
    r = cur.fetchone() or {"vendas":0, "receita":0}

    cur.execute("""
        SELECT p.id, p.quantidade AS qtd_inicial,
               COALESCE(SUM(iv.quantidade),0) AS vendidos
        FROM produtos p
        LEFT JOIN itens_venda iv ON iv.produto_id = p.id
        LEFT JOIN vendas v ON v.id = iv.venda_id AND v.usuario_id = %s
        WHERE p.usuario_id = %s
        GROUP BY p.id
    """, (uid, uid))
    baixo = 0; falta = 0
    for row in cur.fetchall():
        ini = int(row["qtd_inicial"] or 0)
        ven = int(row["vendidos"] or 0)
        est = max(0, ini - ven)
        if est == 0: falta += 1
        if est > 0 and est <= max(1, int(0.2 * ini)): baixo += 1

    cur.close(); conn.close()
    return {"vendas_semana": int(r["vendas"] or 0),
            "receita_semana": float(r["receita"] or 0.0),
            "itens_baixo": baixo, "itens_falta": falta}

@main_bp.route('/')
def home():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    return redirect(url_for('main_bp.dashboard'))

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
            conn = get_db_connection(); cur = conn.cursor()
            preco_base = f.get('preco') or f.get('preco_custo')
            cur.execute("""
                INSERT INTO produtos (nome,preco,preco_custo,preco_venda,quantidade,categoria,subcategoria,tamanho,data_chegada,usuario_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (f['nome'], preco_base, f['preco_custo'], f['preco_venda'], f['quantidade'],
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
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
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
            conn.commit(); flash("Venda registrada com sucesso!")
        except Exception as e:
            print("Erro ao registrar venda:", e)
            conn.rollback(); flash("Erro ao registrar venda.")
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

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
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
        sql += " AND p.categoria = %s"; params.append(categoria_sel)
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
            "id": r['id'], "nome": r['nome'], "categoria": r['categoria'],
            "preco_venda": float(r['preco_venda']), "preco_custo": float(r['preco_custo']),
            "qtd_inicial": int(r['qtd_inicial']), "vendidos": int(r['vendidos']),
            "em_estoque": int(em_estoque), "perc_vendido": perc_vendido, "status": status
        })

    kpis = {"produtos": len(tabela), "itens": int(total_itens),
            "valor_custo": round(total_custo, 2), "valor_venda": round(total_venda, 2)}
    return render_template('ver_estoque.html', produtos=tabela, categorias=categorias,
                           categoria_selecionada=categoria_sel, kpis=kpis)

# =============== DASHBOARD (PÁGINA) ===============
@main_bp.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    email = session.get('usuario_email')

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id=%s", (uid,))
    categorias_db = [r['categoria'] for r in cur.fetchall() if r['categoria']]
    cur.close(); conn.close()
    categorias_csv = _csv_categories_for_email(email)
    categorias = sorted({*categorias_db, *categorias_csv})

    kpis = _kpis_semana(uid)
    return render_template("dashboard.html", kpis=kpis, categorias=categorias)

# =============== DASHBOARD (API JSON) ===============
@main_bp.route('/api/dashboard')
def api_dashboard():
    if 'usuario_id' not in session:
        return jsonify({})
    uid = session['usuario_id']
    email = session.get('usuario_email')
    categoria_sel = request.args.get('categoria', '').strip() or None

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
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
        sql += " AND p.categoria = %s"; params.append(categoria_sel)
    sql += " GROUP BY p.id ORDER BY p.nome"
    cur.execute(sql, tuple(params))
    db_rows = cur.fetchall()
    cur.close(); conn.close()

    csv_rows = _csv_dashboard_rows(uid, email, categoria_sel=categoria_sel)

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

# =============== PREVISÃO (PÁGINA/API) ===============
@main_bp.route('/ver_previsao')
def ver_previsao():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    email = session.get('usuario_email')

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT categoria FROM produtos WHERE usuario_id=%s", (uid,))
    categorias_db = [r['categoria'] for r in cur.fetchall() if r['categoria']]
    cur.close(); conn.close()

    categorias_csv = _csv_categories_for_email(email)
    categorias = sorted({*categorias_db, *categorias_csv})
    categoria_sel = request.args.get('categoria', '').strip()
    return render_template("ver_previsao.html", grafico=None, categorias=categorias, categoria_selecionada=categoria_sel)

@main_bp.route('/api/previsao')
def api_previsao():
    if 'usuario_id' not in session:
        return jsonify({})
    uid = session['usuario_id']
    email = session.get('usuario_email')
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
        sql += " AND p.categoria = %s"; params.append(categoria_sel)
    sql += " GROUP BY DATE(v.data) ORDER BY dia"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()

    csv_daily = _csv_previsao_series(email, categoria_sel)

    from collections import defaultdict
    daily = defaultdict(int)
    for r in rows:
        daily[str(r['dia'])] += int(r['qtd'] or 0)
    for k, v in (csv_daily or {}).items():
        daily[k] += int(v or 0)

    if not daily:
        return jsonify({"labels_hist": [], "hist": [], "labels_pred": [], "pred": []})

    import numpy as np, datetime as _dt
    days_sorted = sorted(daily.keys())
    y = np.array([daily[d] for d in days_sorted], dtype=float)
    n = len(y); t = np.arange(n, dtype=float)

    if n >= 2:
        a, b = np.polyfit(t, y, 1); trend = a * t + b
    else:
        trend = np.full(n, y.mean() if n else 0.0)

    dow_means = {i: [] for i in range(7)}
    for i, d in enumerate(days_sorted):
        dt_obj = _dt.date.fromisoformat(d)
        dow_means[dt_obj.weekday()].append(y[i] - trend[i])
    import numpy as _np
    dow_adj = {k: (_np.mean(v) if v else 0.0) for k, v in dow_means.items()}

    h = 14
    future_days, future_y = [], []
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

# =============== IMPORT CSV (admin) ===============
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
        conn = get_db_connection(); cur = conn.cursor()

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
                    """, (row['id'], row['nome'], row['preco'], row['preco_custo'], row['preco_venda'],
                          row['quantidade'], row['categoria'] or None, row['subcategoria'] or None,
                          row['tamanho'] or None, row['data_chegada'] or None, row['usuario_id']))

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

# =============== LISTA DE COMPRAS (compatível MySQL 5.7+) ===============
@main_bp.route('/lista_compras', methods=['GET'])
def lista_compras():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']

    margem = float(request.args.get('margem') or 30)
    horizonte = int(request.args.get('horizonte') or 7)

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    sql = """
        SELECT
            p.id,
            p.nome,
            p.preco_custo AS custo,
            p.quantidade  AS qtd_inicial,
            COALESCE((
                SELECT SUM(iv2.quantidade)
                FROM vendas v2
                JOIN itens_venda iv2 ON iv2.venda_id = v2.id
                WHERE v2.usuario_id = %s
                  AND iv2.produto_id = p.id
                  AND v2.data >= (CURDATE() - INTERVAL 42 DAY)
            ), 0) AS qtd_42,
            COALESCE((
                SELECT COUNT(DISTINCT DATE(v3.data))
                FROM vendas v3
                JOIN itens_venda iv3 ON iv3.venda_id = v3.id
                WHERE v3.usuario_id = %s
                  AND iv3.produto_id = p.id
                  AND v3.data >= (CURDATE() - INTERVAL 42 DAY)
            ), 0) AS dias_ativos
        FROM produtos p
        WHERE p.usuario_id = %s
        ORDER BY p.nome
    """
    cur.execute(sql, (uid, uid, uid))
    base = cur.fetchall()
    cur.close(); conn.close()

    itens, total = [], 0.0
    for r in base:
        dias = max(1, int(r['dias_ativos'] or 0))
        uso_dia = float(r['qtd_42'] or 0) / dias
        demanda = uso_dia * horizonte * (1.0 + margem/100.0)
        sugerido = max(0, round(demanda - float(r['qtd_inicial'] or 0)))
        if sugerido <= 0: continue
        custo_est = sugerido * float(r['custo'] or 0.0)
        total += custo_est
        itens.append({
            "id": r["id"], "nome": r["nome"], "unidade": "un",
            "sugerido": int(sugerido), "custo": float(r["custo"] or 0.0),
            "custo_estimado": round(custo_est, 2)
        })

    return render_template('lista_compras.html',
                           itens=itens, total=round(total,2),
                           margem=int(margem), horizonte=horizonte)

# =============== RELATÓRIOS (estável) ===============
@main_bp.route('/relatorios', methods=['GET'])
def relatorios():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
            COUNT(DISTINCT v.id) AS total_vendas,
            COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0) AS receita,
            COALESCE(SUM(iv.quantidade * p.preco_custo), 0)      AS custo_total
        FROM vendas v
        LEFT JOIN itens_venda iv ON iv.venda_id = v.id
        LEFT JOIN produtos p     ON p.id = iv.produto_id
        WHERE v.usuario_id = %s
    """, (uid,))
    k = cur.fetchone() or {"total_vendas":0,"receita":0.0,"custo_total":0.0}
    kpi = {
        "total_vendas": int(k["total_vendas"] or 0),
        "receita": float(k["receita"] or 0.0),
        "custo_total": float(k["custo_total"] or 0.0)
    }

    cur.execute("""
        SELECT
            p.id,
            p.nome,
            'un' AS unidade,
            COALESCE(SUM(iv.quantidade), 0) AS uso_total,
            COALESCE(SUM(iv.quantidade * p.preco_custo), 0) AS custo_total
        FROM produtos p
        LEFT JOIN itens_venda iv ON iv.produto_id = p.id
        LEFT JOIN vendas v       ON v.id = iv.venda_id
        WHERE p.usuario_id = %s
          AND (v.data IS NULL OR v.data >= (CURDATE() - INTERVAL 28 DAY))
        GROUP BY p.id, p.nome
        ORDER BY uso_total DESC, p.nome ASC
    """, (uid,))
    consumo = cur.fetchall()

    cur.close(); conn.close()
    return render_template('relatorios.html', kpi=kpi, consumo=consumo)

# =============== ONBOARDING (NEW) ===============
@main_bp.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if 'usuario_id' not in session:
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        biz_type = (request.form.get('biz_type') or '').strip() or 'other'
        lang = (request.form.get('lang') or '').strip() or 'pt'
        if lang not in ('pt', 'en', 'es'): lang = 'pt'
        session['biz_type'] = biz_type
        session['lang'] = lang
        flash(I18N[lang]["Profile saved"])
        return redirect(url_for('main_bp.dashboard'))

    return render_template('onboarding.html')
