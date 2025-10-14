from flask import Blueprint, render_template, request, session, redirect, url_for, abort, jsonify
from tcc_app.db import get_db_connection

restaurant_bp = Blueprint("restaurant_bp", __name__)

def _login_required():
    return 'usuario_id' in session

# ---------------------------
# MENU (itens do restaurante)
# ---------------------------
@restaurant_bp.route("/menu")
def menu():
    if not _login_required():
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']
    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM itens_menu WHERE user_id=%s ORDER BY categoria, nome", (uid,))
    itens = cur.fetchall()
    cur.close(); conn.close()
    return render_template("menu.html", itens=itens)

# --------------------------------------
# INGREDIENTES com classificação (NOVO)
# --------------------------------------
@restaurant_bp.route("/menu/ingredientes")
def ingredientes():
    if not _login_required():
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)

    # consumo médio/dia (30d) por ingrediente
    cur.execute("""
        WITH uso AS (
            SELECT
              r.ingrediente_id,
              SUM(vm.qtd * r.qtd_por_item) AS consumo,
              DATEDIFF(MAX(vm.data), MIN(vm.data)) + 1 AS dias
            FROM vendas_menu vm
            JOIN receita r ON r.user_id = vm.user_id AND r.item_id = vm.item_id
            WHERE vm.user_id = %s AND vm.data >= CURDATE() - INTERVAL 30 DAY
            GROUP BY r.ingrediente_id
        )
        SELECT i.id, i.nome, i.unidade, i.custo_unitario, i.perecivel,
               i.estoque_atual, i.estoque_minimo, i.status,
               COALESCE(u.consumo,0) AS consumo_30,
               COALESCE(u.dias,0) AS dias_observados,
               CASE WHEN COALESCE(u.dias,0) > 0 THEN COALESCE(u.consumo,0) / u.dias ELSE 0 END AS media_dia
        FROM ingredientes i
        LEFT JOIN uso u ON u.ingrediente_id = i.id
        WHERE i.user_id = %s
        ORDER BY i.nome
    """, (uid, uid))
    rows = cur.fetchall()
    cur.close(); conn.close()

    H = 7  # horizonte em dias
    tabela = []
    for r in rows:
        media_dia = float(r["media_dia"] or 0)
        necessidade_7 = media_dia * H
        estoque = float(r["estoque_atual"] or 0)

        if estoque <= 0:
            nivel = "Urgente"
        else:
            base = necessidade_7 if necessidade_7 > 0 else 1
            ratio = estoque / base
            if ratio > 1.5:
                nivel = "Excesso"
            elif ratio >= 0.8:
                nivel = "OK"
            else:
                nivel = "Atenção"

        tabela.append({
            **r,
            "media_dia": round(media_dia, 2),
            "necessidade_7": round(necessidade_7, 2),
            "nivel": nivel
        })

    return render_template("ingredientes.html", itens=tabela, horizonte=H)

# ------------------------------------------------------
# REGISTRAR VENDA (Menu) - simples (usa itens_menu/receita)
# ------------------------------------------------------
@restaurant_bp.route("/menu/registrar_venda", methods=["GET", "POST"])
def registrar_venda_menu():
    if not _login_required():
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nome, preco_venda FROM itens_menu WHERE user_id=%s AND ativo=1 ORDER BY nome", (uid,))
    itens = cur.fetchall()

    if request.method == "POST":
        item_id = request.form.get("item_id")
        qtd = int(request.form.get("qtd") or 1)
        if not item_id:
            cur.close(); conn.close()
            return redirect(url_for('restaurant_bp.registrar_venda_menu'))
        # registra
        cur.execute("INSERT INTO vendas_menu (user_id, item_id, data, qtd) VALUES (%s,%s,CURDATE(),%s)",
                    (uid, item_id, qtd))
        conn.commit()
        cur.close(); conn.close()
        return redirect(url_for('restaurant_bp.registrar_venda_menu'))

    cur.close(); conn.close()
    return render_template("registrar_venda_menu.html", itens=itens)

# ---------------------------
# LISTA DE COMPRAS
# ---------------------------
@restaurant_bp.route("/compras/lista")
def lista_compras():
    if not _login_required():
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']

    margem = float(request.args.get("margem", "0.2") or 0.2)  # 20% padrão
    horizonte = int(request.args.get("h", "7") or 7)

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    # média diária
    cur.execute("""
        WITH uso AS (
            SELECT
              r.ingrediente_id,
              SUM(vm.qtd * r.qtd_por_item) AS consumo,
              DATEDIFF(MAX(vm.data), MIN(vm.data)) + 1 AS dias
            FROM vendas_menu vm
            JOIN receita r ON r.user_id = vm.user_id AND r.item_id = vm.item_id
            WHERE vm.user_id = %s AND vm.data >= CURDATE() - INTERVAL 30 DAY
            GROUP BY r.ingrediente_id
        )
        SELECT i.id, i.nome, i.unidade, i.estoque_atual, i.estoque_minimo, i.custo_unitario,
               COALESCE(u.consumo,0) AS consumo_30,
               CASE WHEN COALESCE(u.dias,0) > 0 THEN COALESCE(u.consumo,0) / u.dias ELSE 0 END AS media_dia
        FROM ingredientes i
        LEFT JOIN uso u ON u.ingrediente_id = i.id
        WHERE i.user_id = %s
        ORDER BY i.nome
    """, (uid, uid))
    rows = cur.fetchall()
    cur.close(); conn.close()

    itens = []
    total_custo = 0.0
    for r in rows:
        media = float(r["media_dia"] or 0.0)
        necessidade = media * horizonte
        necessidade_segura = necessidade * (1.0 + margem)
        comprar = max(0.0, necessidade_segura - float(r["estoque_atual"] or 0.0))
        custo = comprar * float(r["custo_unitario"] or 0.0)
        total_custo += custo
        itens.append({
            **r,
            "media_dia": media,
            "necessidade": necessidade,
            "comprar": comprar,
            "custo_total": custo
        })

    return render_template("lista_compras.html",
                           itens=itens,
                           margem=margem,
                           horizonte=horizonte,
                           total_custo=total_custo)

# ---------------------------
# RELATÓRIOS simples
# ---------------------------
@restaurant_bp.route("/relatorios")
def relatorios():
    if not _login_required():
        return redirect(url_for('auth_bp.login'))
    uid = session['usuario_id']

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
          DATE(vm.data) AS dia,
          SUM(vm.qtd) AS qtde,
          SUM(vm.qtd * im.preco_venda) AS receita
        FROM vendas_menu vm
        JOIN itens_menu im ON im.id = vm.item_id AND im.user_id = vm.user_id
        WHERE vm.user_id = %s
        GROUP BY DATE(vm.data)
        ORDER BY dia DESC
        LIMIT 60
    """, (uid,))
    dias = cur.fetchall()
    cur.close(); conn.close()

    labels = [str(r["dia"]) for r in reversed(dias)]
    qtde   = [int(r["qtde"]) for r in reversed(dias)]
    receit = [float(r["receita"] or 0.0) for r in reversed(dias)]

    return render_template("relatorios.html", labels=labels, qtde=qtde, receita=receit)
