from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from tcc_app.db import get_db_connection

restaurant_bp = Blueprint("restaurant_bp", __name__)

def _require_login():
    return "usuario_id" in session

def _placeholders(n: int) -> str:
    return "(" + ",".join(["%s"] * max(1, n)) + ")"

# ---------- MENU ----------
@restaurant_bp.route("/menu", methods=["GET", "POST"])
def menu():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)

    # criação rápida
    if request.method == "POST" and request.form.get("acao") == "criar":
        nome = (request.form.get("nome") or "").strip()
        preco = request.form.get("preco") or "0"
        if not nome:
            flash("Informe um nome para o item do menu.")
        else:
            try:
                cur.execute("INSERT INTO menu_itens (usuario_id, nome, preco) VALUES (%s,%s,%s)",
                            (uid, nome, float(preco or 0)))
                conn.commit()
                flash("Item do menu criado.")
            except Exception as e:
                conn.rollback(); flash("Falha ao criar item do menu."); print("menu:create ERR:", e)

    # itens de menu
    cur.execute("SELECT id, nome, preco FROM menu_itens WHERE usuario_id=%s ORDER BY nome", (uid,))
    itens = cur.fetchall()

    # produtos para montar receita
    cur.execute("SELECT id, nome, preco_venda, preco_custo FROM produtos WHERE usuario_id=%s ORDER BY nome", (uid,))
    produtos = cur.fetchall()

    # receitas agrupadas por item
    receitas = {}
    if itens:
        ids = [i["id"] for i in itens]
        try:
            cur.execute(f"""
                SELECT r.id, r.menu_item_id, r.produto_id, r.qtd_por_item, p.nome AS produto_nome
                FROM receitas r
                JOIN produtos p ON p.id = r.produto_id
                WHERE r.menu_item_id IN {_placeholders(len(ids))}
            """, tuple(ids))
            for row in cur.fetchall():
                receitas.setdefault(row["menu_item_id"], []).append(row)
        except Exception as e:
            print("load receitas ERR:", e)
            receitas = {}

    cur.close(); conn.close()
    return render_template("menu.html", itens=itens, produtos=produtos, receitas=receitas)

@restaurant_bp.route("/menu/receita/add", methods=["POST"])
def menu_receita_add():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    item_id = request.form.get("menu_item_id")
    produto_id = request.form.get("produto_id")
    qtd = request.form.get("qtd_por_item")

    if not (item_id and produto_id and qtd):
        flash("Preencha item, produto e quantidade.")
        return redirect(url_for("restaurant_bp.menu"))

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM menu_itens WHERE id=%s AND usuario_id=%s", (item_id, uid))
    if not cur.fetchone():
        cur.close(); conn.close(); flash("Item não encontrado.")
        return redirect(url_for("restaurant_bp.menu"))

    try:
        cur.execute("INSERT INTO receitas (menu_item_id, produto_id, qtd_por_item) VALUES (%s,%s,%s)",
                    (item_id, produto_id, float(qtd)))
        conn.commit(); flash("Ingrediente adicionado à receita.")
    except Exception as e:
        conn.rollback(); flash("Falha ao adicionar ingrediente."); print("menu_receita_add ERR:", e)
    finally:
        cur.close(); conn.close()

    return redirect(url_for("restaurant_bp.menu"))

@restaurant_bp.route("/menu/receita/del/<int:receita_id>", methods=["POST"])
def menu_receita_del(receita_id: int):
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.id
        FROM receitas r
        JOIN menu_itens m ON m.id = r.menu_item_id
        WHERE r.id=%s AND m.usuario_id=%s
    """, (receita_id, uid))
    if not cur.fetchone():
        cur.close(); conn.close(); flash("Receita não encontrada.")
        return redirect(url_for("restaurant_bp.menu"))

    try:
        cur.execute("DELETE FROM receitas WHERE id=%s", (receita_id,))
        conn.commit(); flash("Ingrediente removido.")
    except Exception as e:
        conn.rollback(); flash("Falha ao remover ingrediente."); print("menu_receita_del ERR:", e)
    finally:
        cur.close(); conn.close()

    return redirect(url_for("restaurant_bp.menu"))

# ---------- REGISTRAR VENDA A PARTIR DO MENU ----------
@restaurant_bp.route("/registrar_venda_menu", methods=["GET", "POST"])
def registrar_venda_menu():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        menu_item_id = request.form.get("menu_item_id")
        qtd = int(request.form.get("quantidade") or 0)
        data_venda = request.form.get("data_venda")
        if not (menu_item_id and qtd and data_venda):
            flash("Preencha item, quantidade e data.")
            cur.close(); conn.close()
            return redirect(url_for("restaurant_bp.registrar_venda_menu"))

        cur.execute("""
            SELECT r.produto_id, r.qtd_por_item, p.preco_venda
            FROM receitas r
            JOIN produtos p ON p.id = r.produto_id
            JOIN menu_itens m ON m.id = r.menu_item_id
            WHERE r.menu_item_id=%s AND m.usuario_id=%s
        """, (menu_item_id, uid))
        receita = cur.fetchall()
        if not receita:
            flash("Este item de menu não tem receita cadastrada.")
            cur.close(); conn.close()
            return redirect(url_for("restaurant_bp.registrar_venda_menu"))

        try:
            cur.execute("INSERT INTO vendas (usuario_id, data) VALUES (%s,%s)", (uid, data_venda))
            venda_id = cur.lastrowid
            for r in receita:
                cur.execute("""
                    INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
                    VALUES (%s,%s,%s,%s)
                """, (venda_id, r["produto_id"], float(r["qtd_por_item"]) * qtd, float(r["preco_venda"])))
            conn.commit(); flash("Venda registrada a partir do menu!")
        except Exception as e:
            conn.rollback(); flash("Falha ao registrar venda."); print("registrar_venda_menu ERR:", e)
        finally:
            cur.close(); conn.close()

        return redirect(url_for("restaurant_bp.registrar_venda_menu"))

    cur.execute("SELECT id, nome, preco FROM menu_itens WHERE usuario_id=%s ORDER BY nome", (uid,))
    itens = cur.fetchall()
    cur.close(); conn.close()
    return render_template("registrar_venda_menu.html", itens=itens)

# ---------- LISTA DE COMPRAS / RELATÓRIOS ----------
@restaurant_bp.route("/lista_compras")
def lista_compras():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    margem = int(request.args.get("margem") or 20)       # % segurança
    horizonte = int(request.args.get("horizonte") or 7)  # dias

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.id, p.nome, 'un' AS unidade, p.preco_custo AS custo,
               p.quantidade AS qtd_inicial,
               COALESCE(SUM(iv.quantidade),0) AS vendidos
        FROM produtos p
        LEFT JOIN itens_venda iv ON iv.produto_id = p.id
        LEFT JOIN vendas v ON v.id = iv.venda_id AND v.usuario_id = %s
        WHERE p.usuario_id = %s
        GROUP BY p.id
        ORDER BY p.nome
    """, (uid, uid))
    rows = cur.fetchall()

    cur.execute("""
        SELECT iv.produto_id, SUM(iv.quantidade) AS qtd_28d
        FROM itens_venda iv
        JOIN vendas v ON v.id = iv.venda_id
        WHERE v.usuario_id = %s AND v.data >= (CURRENT_DATE - INTERVAL 28 DAY)
        GROUP BY iv.produto_id
    """, (uid,))
    consumo_28 = {r["produto_id"]: int(r["qtd_28d"] or 0) for r in cur.fetchall()}

    itens, total = [], 0.0
    for r in rows:
        estoque_atual = max(0, int(r["qtd_inicial"] or 0) - int(r["vendidos"] or 0))
        media_dia = consumo_28.get(r["id"], 0) / 28.0
        necessidade = max(0.0, media_dia * horizonte - estoque_atual)
        necessidade *= (1 + margem/100.0)
        sugerido = int(round(necessidade))

        if sugerido > 0:
            custo_est = sugerido * float(r["custo"] or 0.0)
            total += custo_est
            itens.append({
                "nome": r["nome"],
                "unidade": r["unidade"],
                "sugerido": sugerido,
                "custo": float(r["custo"] or 0.0),
                "custo_estimado": round(custo_est, 2),
            })

    cur.close(); conn.close()
    return render_template("lista_compras.html",
                           itens=itens, total=round(total,2),
                           margem=margem, horizonte=horizonte)

@restaurant_bp.route("/relatorios")
def relatorios():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT COUNT(DISTINCT v.id) AS total_vendas,
               COALESCE(SUM(iv.quantidade * iv.preco_unitario),0) AS receita
        FROM vendas v
        LEFT JOIN itens_venda iv ON iv.venda_id = v.id
        WHERE v.usuario_id = %s
    """, (uid,))
    kpi = cur.fetchone() or {"total_vendas":0, "receita":0.0}

    cur.execute("""
        SELECT p.nome, 'un' AS unidade, p.preco_custo AS custo,
               COALESCE(SUM(iv.quantidade),0) AS uso_total,
               COALESCE(SUM(iv.quantidade * p.preco_custo),0) AS custo_total
        FROM produtos p
        LEFT JOIN itens_venda iv ON iv.produto_id = p.id
        LEFT JOIN vendas v ON v.id = iv.venda_id AND v.usuario_id = %s
        WHERE p.usuario_id = %s
          AND (v.data IS NULL OR v.data >= (CURRENT_DATE - INTERVAL 28 DAY))
        GROUP BY p.id
        ORDER BY p.nome
    """, (uid, uid))
    consumo = cur.fetchall()

    cur.close(); conn.close()
    return render_template("relatorios.html", kpi=kpi, consumo=consumo)
