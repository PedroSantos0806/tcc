from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from tcc_app.utils import login_required, MEM, get_produto, add_produto, add_venda, add_item_venda
import pandas as pd
from sklearn.linear_model import Ridge
from datetime import timedelta
import numpy as np

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
@login_required
def home():
    return render_template('home.html', nome=session.get('usuario_nome'))

# ---------- CADASTRAR PRODUTO ----------
@main_bp.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    if request.method == 'POST':
        form = request.form
        obrig = ['nome','preco','preco_custo','preco_venda','quantidade','categoria','data_chegada']
        if any(not form.get(k) for k in obrig):
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('main_bp.cadastrar_produto'))
        try:
            add_produto({
                "nome": form.get('nome'),
                "preco": float(form.get('preco')),
                "preco_custo": float(form.get('preco_custo')),
                "preco_venda": float(form.get('preco_venda')),
                "quantidade": int(form.get('quantidade')),
                "categoria": form.get('categoria'),
                "subcategoria": form.get('subcategoria') or "",
                "tamanho": form.get('tamanho') or "",
                "data_chegada": form.get('data_chegada'),
                "usuario_id": session['usuario_id']
            })
            flash('Produto cadastrado com sucesso!')
        except Exception as e:
            print("Erro ao cadastrar produto:", e)
            flash('Erro ao cadastrar produto.')
        return redirect(url_for('main_bp.cadastrar_produto'))
    return render_template('cadastrar_produto.html')

# ---------- CADASTRAR VENDA ----------
@main_bp.route('/cadastrar_venda', methods=['GET', 'POST'])
@login_required
def cadastrar_venda():
    usuario_id = session['usuario_id']
    produtos = [p for p in MEM["produtos"] if p["usuario_id"] == usuario_id]
    if request.method == 'POST':
        data_venda = request.form.get('data_venda')
        ids = request.form.getlist('produto_id[]')
        qtds = request.form.getlist('quantidade[]')
        if not data_venda or not ids or not qtds:
            flash("Preencha todos os campos.")
            return redirect(url_for('main_bp.cadastrar_venda'))
        try:
            v = add_venda(usuario_id, data_venda)
            for pid, q in zip(ids, qtds):
                if not pid or not q: continue
                p = get_produto(int(pid))
                if not p: continue
                add_item_venda(v["id"], p["id"], int(q), p["preco_venda"])
            flash("Venda registrada com sucesso!")
        except Exception as e:
            print("Erro ao registrar venda:", e)
            flash("Erro ao registrar venda.")
        return redirect(url_for('main_bp.cadastrar_venda'))
    return render_template("registrar_venda.html", produtos=produtos)

# ---------- ESTOQUE ----------
@main_bp.route('/ver_estoque')
@login_required
def ver_estoque():
    uid = session['usuario_id']
    produtos = [p for p in MEM["produtos"] if p["usuario_id"] == uid]
    vendidos = {}
    for it in MEM["itens_venda"]:
        v = next((x for x in MEM["vendas"] if x["id"] == it["venda_id"]), None)
        if not v or v["usuario_id"] != uid: continue
        vendidos[it["produto_id"]] = vendidos.get(it["produto_id"], 0) + it["quantidade"]
    tabela = []
    for p in produtos:
        vnd = vendidos.get(p["id"], 0)
        tabela.append({
            "id": p["id"], "nome": p["nome"], "categoria": p["categoria"],
            "subcategoria": p["subcategoria"], "tamanho": p["tamanho"],
            "preco": p["preco"], "qtd_inicial": p["quantidade"], "vendidos": vnd,
            "quantidade_atual": max(0, p["quantidade"] - vnd)
        })
    return render_template('ver_estoque.html', produtos=tabela)

# ---------- DASHBOARD (PÁGINA) ----------
@main_bp.route('/dashboard')
@login_required
def dashboard():
    uid = session['usuario_id']
    produtos_user = [p for p in MEM["produtos"] if p["usuario_id"] == uid]
    categorias = sorted({p["categoria"] for p in produtos_user})
    categoria_sel = request.args.get('categoria', '').strip()
    return render_template("dashboard.html", categorias=categorias, categoria_selecionada=categoria_sel,
                           nomes=[], vendidos=[], em_estoque=[], custo=[], lucro=[])

# ---------- DASHBOARD (API JSON PARA CHART.JS) ----------
@main_bp.route('/api/dashboard')
@login_required
def api_dashboard():
    uid = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip()
    prods = [p for p in MEM["produtos"] if p["usuario_id"] == uid]
    if categoria_sel:
        prods = [p for p in prods if p["categoria"] == categoria_sel]

    vendidos, receita, custo = {}, {}, {}
    for it in MEM["itens_venda"]:
        v = next((x for x in MEM["vendas"] if x["id"] == it["venda_id"]), None)
        p = next((x for x in prods if x["id"] == it["produto_id"]), None)
        if not v or not p or v["usuario_id"] != uid: continue
        pid = p["id"]
        vendidos[pid] = vendidos.get(pid, 0) + it["quantidade"]
        receita[pid] = receita.get(pid, 0.0) + it["quantidade"] * it["preco_unitario"]
        custo[pid] = custo.get(pid, 0.0) + it["quantidade"] * float(p["preco_custo"])

    labels, vnds, estq, cst, lcr = [], [], [], [], []
    for p in prods:
        pid = p["id"]
        qvend = vendidos.get(pid, 0)
        labels.append(p["nome"])
        vnds.append(qvend)
        estq.append(max(0, int(p["quantidade"]) - int(qvend)))
        ct = round(custo.get(pid, 0.0), 2)
        rc = round(receita.get(pid, 0.0), 2)
        cst.append(ct)
        lcr.append(round(rc - ct, 2))
    return jsonify({"labels": labels, "vendidos": vnds, "estoque": estq, "custo": cst, "lucro": lcr})

# ---------- PREVISÃO (PÁGINA) ----------
@main_bp.route('/ver_previsao')
@login_required
def ver_previsao():
    uid = session['usuario_id']
    prods = [p for p in MEM["produtos"] if p["usuario_id"] == uid]
    categorias = sorted({p["categoria"] for p in prods})
    categoria_sel = request.args.get('categoria', '').strip()
    return render_template("ver_previsao.html", grafico=None, categorias=categorias, categoria_selecionada=categoria_sel)

# ---------- PREVISÃO (API JSON PARA CHART.JS) ----------
@main_bp.route('/api/previsao')
@login_required
def api_previsao():
    uid = session['usuario_id']
    categoria_sel = request.args.get('categoria', '').strip()

    # monta série diária total (ou por categoria)
    rows = []
    for it in MEM["itens_venda"]:
        v = next((x for x in MEM["vendas"] if x["id"] == it["venda_id"]), None)
        if not v or v["usuario_id"] != uid: continue
        p = next((x for x in MEM["produtos"] if x["id"] == it["produto_id"]), None)
        if not p: continue
        if categoria_sel and p["categoria"] != categoria_sel: continue
        rows.append({"data": v["data"].date().isoformat(), "qtd": it["quantidade"]})

    if not rows:
        return jsonify({"labels": [], "hist": [], "pred": []})

    df = pd.DataFrame(rows)
    s = df.groupby("data")["qtd"].sum().sort_index()
    s.index = pd.to_datetime(s.index)

    # features simples: tendência + dummies de dia da semana
    X = pd.DataFrame({"t": np.arange(len(s)), "dow": s.index.dayofweek}, index=s.index)
    X = pd.get_dummies(X, columns=["dow"], drop_first=True)
    y = s.values

    model = Ridge(alpha=1.0)
    model.fit(X, y)

    # horizonte = 14 dias
    h = 14
    fut_idx = pd.date_range(s.index.max() + pd.Timedelta(days=1), periods=h, freq="D")
    Xf = pd.DataFrame({"t": np.arange(len(s), len(s)+h), "dow": fut_idx.dayofweek}, index=fut_idx)
    Xf = pd.get_dummies(Xf, columns=["dow"], drop_first=True).reindex(columns=X.columns, fill_value=0)
    y_lr = model.predict(Xf)

    # blend com média móvel 7
    ma7 = s.rolling(7, min_periods=1).mean().iloc[-1]
    y_pred = np.clip(0.7*y_lr + 0.3*ma7, 0, None)

    labels_hist = s.index.strftime("%Y-%m-%d").tolist()[-60:]  # últimos 60 dias
    hist_vals = s.values.tolist()[-60:]
    labels_fut = fut_idx.strftime("%Y-%m-%d").tolist()
    pred_vals = y_pred.round(2).tolist()

    return jsonify({"labels_hist": labels_hist, "hist": hist_vals, "labels_pred": labels_fut, "pred": pred_vals})
