# tcc_app/routes/restaurant_routes.py
from __future__ import annotations
from datetime import date, timedelta
from collections import defaultdict, Counter
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from tcc_app.db import get_db_connection

restaurant_bp = Blueprint("restaurant_bp", __name__, url_prefix="/restaurante")

# -----------------------------
# Helpers
# -----------------------------
def _uid():
    return session.get("usuario_id")

def _as_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return float(default)

def _as_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return int(default)

# =====================================================================
# INGREDIENTES
# =====================================================================
@restaurant_bp.route("/ingredientes", methods=["GET", "POST"])
def ingredientes():
    if not _uid():
        return redirect(url_for("auth_bp.login"))
    uid = _uid()
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        f = request.form
        cur.execute(
            """
            INSERT INTO ingredientes
              (usuario_id, nome, unidade, custo, perecivel, estoque_atual, estoque_minimo)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                uid,
                f.get("nome") or "",
                f.get("unidade") or "",
                _as_float(f.get("custo")),
                1 if (f.get("perecivel") == "1") else 0,
                _as_int(f.get("estoque_atual")),
                _as_int(f.get("estoque_minimo")),
            ),
        )
        conn.commit()
        flash("Ingrediente cadastrado.")
        cur.close()
        conn.close()
        return redirect(url_for("restaurant_bp.ingredientes"))

    cur.execute(
        "SELECT * FROM ingredientes WHERE usuario_id=%s ORDER BY nome",
        (uid,),
    )
    ingredientes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("ingredientes.html", ingredientes=ingredientes)

# =====================================================================
# MENU (itens vendidos) + RECEITAS (decomposição por ingrediente)
# =====================================================================
@restaurant_bp.route("/menu", methods=["GET", "POST"])
def menu():
    if not _uid():
        return redirect(url_for("auth_bp.login"))
    uid = _uid()
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        f = request.form
        cur.execute(
            """
            INSERT INTO menu_itens (usuario_id, nome, preco, ativo)
            VALUES (%s,%s,%s,%s)
            """,
            (uid, f.get("nome") or "", _as_float(f.get("preco")), 1),
        )
        conn.commit()
        flash("Item de menu cadastrado.")
        cur.close()
        conn.close()
        return redirect(url_for("restaurant_bp.menu"))

    # lista itens e suas receitas
    cur.execute("SELECT * FROM menu_itens WHERE usuario_id=%s ORDER BY ativo DESC, nome", (uid,))
    itens = cur.fetchall()

    # carrega ingredientes para montar receitas
    cur.execute("SELECT id, nome, unidade FROM ingredientes WHERE usuario_id=%s ORDER BY nome", (uid,))
    ingredientes = cur.fetchall()

    # receitas agrupadas
    cur.execute(
        """
        SELECT r.item_id, r.ingrediente_id, r.quantidade, i.nome AS ing_nome, i.unidade
        FROM receitas r
        JOIN ingredientes i ON i.id = r.ingrediente_id
        WHERE r.usuario_id=%s
        """,
        (uid,),
    )
    rows = cur.fetchall()
    receitas = defaultdict(list)
    for r in rows:
        receitas[r["item_id"]].append(r)

    cur.close()
    conn.close()
    return render_template("menu.html", itens=itens, ingredientes=ingredientes, receitas=receitas)

@restaurant_bp.route("/menu/receita/add", methods=["POST"])
def receita_add():
    if not _uid():
        return redirect(url_for("auth_bp.login"))
    uid = _uid()
    f = request.form
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO receitas (usuario_id, item_id, ingrediente_id, quantidade)
        VALUES (%s,%s,%s,%s)
        """,
        (uid, _as_int(f.get("item_id")), _as_int(f.get("ingrediente_id")), _as_float(f.get("quantidade"))),
    )
    conn.commit()
    cur.close()
    conn.close()
    flash("Ingrediente adicionado à receita.")
    return redirect(url_for("restaurant_bp.menu"))

@restaurant_bp.route("/menu/receita/del/<int:rid>", methods=["POST"])
def receita_del(rid: int):
    if not _uid():
        return redirect(url_for("auth_bp.login"))
    uid = _uid()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM receitas WHERE usuario_id=%s AND id=%s", (uid, rid))
    conn.commit()
    cur.close()
    conn.close()
    flash("Ingrediente removido da receita.")
    return redirect(url_for("restaurant_bp.menu"))

# =====================================================================
# REGISTRAR VENDA (pelo menu) -> debita ingredientes via receita
# =====================================================================
@restaurant_bp.route("/registrar-venda-menu", methods=["GET", "POST"])
def registrar_venda_menu():
    if not _uid():
        return redirect(url_for("auth_bp.login"))
    uid = _uid()
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # carrega itens de menu ativos
    cur.execute("SELECT * FROM menu_itens WHERE usuario_id=%s AND ativo=1 ORDER BY nome", (uid,))
    itens = cur.fetchall()

    if request.method == "POST":
        data_venda = request.form.get("data_venda") or date.today().isoformat()
        # cria venda "lógica" p/ rastreio
        cur.execute("INSERT INTO vendas (usuario_id, data) VALUES (%s,%s)", (uid, data_venda))
        venda_id = cur.lastrowid

        # mapeia receitas por item
        cur.execute(
            "SELECT * FROM receitas WHERE usuario_id=%s",
            (uid,),
        )
        rec = cur.fetchall()
        receitas = defaultdict(list)
        for r in rec:
            receitas[r["item_id"]].append(r)

        # para cada item enviado
        posted = []
        for k, v in request.form.items():
            if not k.startswith("qtd_"):
                continue
            item_id = _as_int(k.replace("qtd_", ""))
            qtd = _as_int(v)
            if qtd <= 0:
                continue
            posted.append((item_id, qtd))

        # debita ingredientes conforme receitas
        for item_id, qtd in posted:
            # salva em itens_venda (vincula a um produto "sintético" de menu_itens)
            cur.execute(
                "INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario) VALUES (%s,%s,%s,%s)",
                (venda_id, None, qtd, 0.0),
            )
            # debita estoque
            for r in receitas.get(item_id, []):
                cur.execute(
                    """
                    UPDATE ingredientes
                    SET estoque_atual = GREATEST(0, estoque_atual - %s)
                    WHERE id=%s AND usuario_id=%s
                    """,
                    (_as_float(r["quantidade"]) * qtd, r["ingrediente_id"], uid),
                )

        conn.commit()
        flash("Venda registrada e ingredientes debitados.")
        cur.close()
        conn.close()
        return redirect(url_for("restaurant_bp.registrar_venda_menu"))

    cur.close()
    conn.close()
    return render_template("registrar_venda_menu.html", itens=itens)

# =====================================================================
# LISTA DE COMPRAS (baseada em previsão + margem de segurança)
# =====================================================================
@restaurant_bp.route("/lista-compras")
def lista_compras():
    if not _uid():
        return redirect(url_for("auth_bp.login"))
    uid = _uid()
    margem = _as_int(request.args.get("margem", 20))  # %
    dias = _as_int(request.args.get("horizonte", 7))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # consumo histórico por ingrediente (últimas 4 semanas)
    cur.execute(
        """
        SELECT r.ingrediente_id, SUM(iv.quantidade * r.quantidade) AS uso
        FROM itens_venda iv
        JOIN vendas v ON v.id = iv.venda_id AND v.usuario_id=%s
        JOIN receitas r ON r.item_id = iv.produto_id OR r.item_id IS NOT NULL
        WHERE v.data >= DATE_SUB(CURDATE(), INTERVAL 28 DAY) AND r.usuario_id=%s
        GROUP BY r.ingrediente_id
        """,
        (uid, uid),
    )
    rows = cur.fetchall()
    uso_medio_diario = {r["ingrediente_id"]: (float(r["uso"] or 0.0) / 28.0) for r in rows}

    # ingredientes atuais
    cur.execute("SELECT * FROM ingredientes WHERE usuario_id=%s", (uid,))
    ingredientes = cur.fetchall()

    sugestoes = []
    for ing in ingredientes:
        media = uso_medio_diario.get(ing["id"], 0.0)
        demanda = media * dias
        demanda *= (1.0 + margem / 100.0)
        falta = max(0.0, demanda - float(ing["estoque_atual"] or 0.0))
        if falta > 0.0:
            sugestoes.append(
                {
                    "id": ing["id"],
                    "nome": ing["nome"],
                    "unidade": ing["unidade"],
                    "custo": float(ing["custo"] or 0.0),
                    "sugerido": round(falta, 2),
                    "custo_estimado": round(falta * float(ing["custo"] or 0.0), 2),
                }
            )

    total = round(sum(x["custo_estimado"] for x in sugestoes), 2)
    cur.close()
    conn.close()
    return render_template(
        "lista_compras.html",
        itens=sugestoes,
        margem=margem,
        horizonte=dias,
        total=total,
    )

# =====================================================================
# RELATÓRIOS (uso / custo por ingrediente + KPIs)
# =====================================================================
@restaurant_bp.route("/relatorios")
def relatorios():
    if not _uid():
        return redirect(url_for("auth_bp.login"))
    uid = _uid()
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # KPIs simples
    cur.execute(
        """
        SELECT 
            COUNT(*) AS total_vendas,
            COALESCE(SUM(iv.quantidade * iv.preco_unitario),0) AS receita
        FROM vendas v 
        LEFT JOIN itens_venda iv ON iv.venda_id = v.id
        WHERE v.usuario_id=%s
        """,
        (uid,),
    )
    kpi = cur.fetchone() or {"total_vendas": 0, "receita": 0.0}

    # custo por ingrediente (últimas 4 semanas)
    cur.execute(
        """
        SELECT i.nome, i.unidade, i.custo,
               COALESCE(SUM(r.quantidade * iv.quantidade),0) AS uso_total
        FROM ingredientes i
        LEFT JOIN receitas r ON r.ingrediente_id = i.id AND r.usuario_id=%s
        LEFT JOIN itens_venda iv ON iv.produto_id = r.item_id
        LEFT JOIN vendas v ON v.id = iv.venda_id AND v.usuario_id=%s
        WHERE v.data >= DATE_SUB(CURDATE(), INTERVAL 28 DAY) OR v.id IS NULL
        GROUP BY i.id
        ORDER BY uso_total DESC, i.nome
        """,
        (uid, uid),
    )
    consumo = cur.fetchall()
    for c in consumo:
        c["custo_total"] = round(float(c["uso_total"] or 0.0) * float(c["custo"] or 0.0), 2)

    cur.close()
    conn.close()
    return render_template("relatorios.html", kpi=kpi, consumo=consumo)
