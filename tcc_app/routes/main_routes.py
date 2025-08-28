# tcc_app/routes/main_routes.py
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, abort
from tcc_app.utils import login_required
from tcc_app.db import get_db_connection
from datetime import date, datetime, timedelta
import os, csv

main_bp = Blueprint('main_bp', __name__)

# =============== HELPERS ===============
def _categorias_do_usuario(uid: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT DISTINCT COALESCE(NULLIF(categoria,''),'Sem categoria')
                   FROM produtos WHERE usuario_id=%s ORDER BY 1""", (uid,))
    cats = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return cats

def _serie_diaria(uid: int, categoria: str | None, dias_hist: int = 60):
    """
    Série diária dos últimos N dias (preenchendo zeros nos dias sem venda).
    Soma todas as vendas do usuário (filtrando por categoria se fornecida).
    Retorna: (labels_ddmm, valores)
    """
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    sql = """
      SELECT DATE(v.data) AS d, SUM(iv.quantidade) AS q
      FROM vendas v
      JOIN itens_venda iv ON iv.venda_id = v.id
      JOIN produtos   p ON p.id = iv.produto_id
      WHERE v.usuario_id=%s
    """
    params = [uid]
    if categoria:
        sql += " AND p.categoria=%s"
        params.append(categoria)
    sql += " GROUP BY DATE(v.data) ORDER BY d"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()

    if not rows:
        return [], []

    last_day = rows[-1]['d']
    first_day = last_day - timedelta(days=dias_hist-1)
    by_day = {r['d']: int(r['q'] or 0) for r in rows}

    labels, vals = [], []
    d = first_day
    while d <= last_day:
        labels.append(d.strftime("%d/%m"))
        vals.append(by_day.get(d, 0))
        d += timedelta(days=1)
    return labels, vals, last_day

def _forecast_light(hist: list[int | float], horizon: int = 14):
    """
    Previsão leve: regressão linear + ajuste semanal aproximado + MM7.
    Sem dependências pesadas; ótimo para protótipo/TCC.
    """
    import math
    n = len(hist)
    if n == 0:
        return [0]*horizon
    if n == 1:
        return [hist[0]]*horizon

    # tendência linear por mínimos quadrados fechados
    x = list(range(n))
    sumx = sum(x); sumy = sum(hist)
    sumxy = sum(i*y for i, y in enumerate(hist))
    sumx2 = sum(i*i for i in x)
    denom = n*sumx2 - sumx*sumx
    if denom == 0:
        a = sumy/n; b = 0.0
    else:
        b = (n*sumxy - sumx*sumy) / denom
        a = (sumy - b*sumx) / n

    mm7 = sum(hist[-min(7, n):]) / min(7, n)

    # sem datas reais aqui (dia da semana), usamos apenas suavização
    preds = []
    for k in range(1, horizon+1):
        y = a + b*(n-1 + k)
        y = 0.7*y + 0.3*mm7
        preds.append(max(0, round(y, 2)))
    return preds

# =============== HOME ===============
@main_bp.route('/')
@login_required
def home():
    return render_template('home.html', nome=session.get('usuario_nome'))

# =============== CADASTRAR PRODUTO ===============
@main_bp.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'POST':
        f = request.form
        obrig = ['nome','preco_custo','preco_venda','quantidade','categoria','data_chegada']
        if any(not f.get(k) for k in obrig):
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_produto'))
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO produtos
                (nome, preco, preco_custo, preco_venda, quantidade, categoria, subcategoria, tamanho, data_chegada, usuario_id)
                VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (f['nome'], f['preco_custo'], f['preco_venda'], f['quantidade'],
                  f['categoria'], f.get('subcategoria') or None, f.get('tamanho') or None,
                  f['data_chegada'], session['usuario_id']))
            conn.commit()
            flash('Produto cadastrado com sucesso!')
        except Exception as e:
            print("Erro ao cadastrar produto:", e)
            conn.rollback()
            flash('Erro ao cadastrar produto.')
        finally:
            try:
                cur.close(); conn.close()
            except:
                pass
        return redirect(url_for('main_bp.cadastrar_produto'))
    return render_template('cadastrar_produto.html')

# =============== CADASTRAR VENDA ===============
@main_bp.route('/cadastrar_venda', methods=['GET', 'POST'])
@login_required
def cadastrar_venda():
    uid = session['usuario_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nome, preco_venda FROM produtos WHERE usuario_id=%s ORDER BY nome", (uid,))
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
        finally:
            cur.close(); conn.close()
        return redirect(url_for('main_bp.cadastrar_venda'))

    cur.close(); conn.close()
    return render_template("registrar_venda.html", produtos=produtos)

# =============== ESTOQUE (PÁGINA) ===============
@main_bp.route('/ver_estoque')
@login_required
def ver_estoque():
    uid = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip() or None

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    categorias = _categorias_do_usuario(uid)

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
    return render_template('ver_estoque.html',
                           produtos=tabela,
                           categorias=categorias,
                           categoria_selecionada=categoria_sel,
                           kpis=kpis)

# =============== DASHBOARD (PÁGINA) ===============
@main_bp.route('/dashboard')
@login_required
def dashboard():
    uid = session['usuario_id']
    categorias = _categorias_do_usuario(uid)
    categoria_sel = request.args.get('categoria', '').strip()
    return render_template("dashboard.html",
                           categorias=categorias,
                           categoria_selecionada=categoria_sel,
                           nomes=[], vendidos=[], em_estoque=[], custo=[], lucro=[])

# =============== DASHBOARD (API JSON) ===============
@main_bp.route('/api/dashboard')
@login_required
def api_dashboard():
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
@login_required
def ver_previsao():
    uid = session['usuario_id']
    categorias = _categorias_do_usuario(uid)
    categoria_sel = request.args.get('categoria', '').strip()
    return render_template("ver_previsao.html",
                           categorias=categorias,
                           categoria_selecionada=categoria_sel)

# =============== PREVISÃO (API JSON) ===============
@main_bp.route('/api/previsao')
@login_required
def api_previsao():
    uid = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip() or None

    labels_hist, hist, last_day = _serie_diaria(uid, categoria_sel, dias_hist=60)
    if not labels_hist:
        return jsonify({"labels_hist": [], "hist": [], "labels_pred": [], "pred": []})

    # previsão de 14 dias a partir do último dia observado
    horizon = 14
    preds = _forecast_light(hist, horizon=horizon)
    labels_pred = []
    d = last_day + timedelta(days=1)
    for _ in range(horizon):
        labels_pred.append(d.strftime("%d/%m"))
        d += timedelta(days=1)

    return jsonify({
        "labels_hist": labels_hist,
        "hist": hist,
        "labels_pred": labels_pred,
        "pred": preds
    })

# =============== IMPORTAR CSV -> MYSQL (admin) ===============
@main_bp.route('/admin/import_csv', methods=['GET', 'POST'])
@login_required
def import_csv():
    # permite admin por e-mail OU usuario_id == 1
    if not (session.get('usuario_email') == 'admin@demo.com' or session.get('usuario_id') == 1):
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
        flash("Importação dos CSVs concluída!")
    except Exception as e:
        print("Erro ao importar CSV:", e)
        conn.rollback()
        flash("Erro ao importar CSV. Veja os logs.")
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

    if request.method == 'POST':
        return redirect(url_for('main_bp.home'))
    return render_template('admin_import.html')

# =============== DIAGNÓSTICO RÁPIDO ===============
@main_bp.route('/debug/db_info')
def debug_db_info():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DATABASE(), @@hostname")
        db, host = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM usuarios"); u = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM produtos"); p = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM vendas"); v = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM itens_venda"); iv = cur.fetchone()[0]
        cur.close(); conn.close()
        return f"DB={db} host={host} | usuarios={u}, produtos={p}, vendas={v}, itens_venda={iv}"
    except Exception as e:
        return f"Erro ao conectar: {e}", 500
