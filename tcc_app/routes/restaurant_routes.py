from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from tcc_app.db import get_db_connection

restaurant_bp = Blueprint("restaurant_bp", __name__)

def _require_login():
    return "usuario_id" in session

# ---------------------------------------
# MENU – listar, criar e montar receita
# ---------------------------------------
@restaurant_bp.route("/menu", methods=["GET", "POST"])
def menu():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Criação rápida de item (nome + preço)
    if request.method == "POST" and request.form.get("acao") == "criar":
        nome = (request.form.get("nome") or "").strip()
        preco = request.form.get("preco") or "0"
        if not nome:
            flash("Informe um nome para o item do menu.")
        else:
            try:
                cur.execute(
                    "INSERT INTO menu_itens (usuario_id, nome, preco) VALUES (%s,%s,%s)",
                    (uid, nome, float(preco or 0.0)),
                )
                conn.commit()
                flash("Item do menu criado.")
            except Exception as e:
                conn.rollback()
                flash("Falha ao criar item do menu.")
                print("menu:create ERR:", e)

    # dados para tela
    cur.execute("SELECT id, nome, preco FROM menu_itens WHERE usuario_id=%s ORDER BY nome", (uid,))
    itens = cur.fetchall()

    # produtos para montar receita
    cur.execute(
        "SELECT id, nome, preco_venda, preco_custo FROM produtos WHERE usuario_id=%s ORDER BY nome",
        (uid,),
    )
    produtos = cur.fetchall()

    # receitas por item (mapa id_item -> lista de ingredientes)
    receitas = {}
    if itens:
        ids = tuple(i["id"] for i in itens)
        # parametrização segura para 1 ou mais ids
        if len(ids) == 1:
            cur.execute(
                """
                SELECT r.id, r.menu_item_id, r.produto_id, r.qtd_por_item, p.nome AS produto_nome
                FROM receitas r
                JOIN produtos p ON p.id = r.produto_id
                WHERE r.menu_item_id IN (%s)
                """,
                ids,
            )
        else:
            placeholders = ",".join(["%s"] * len(ids))
            cur.execute(
                f"""
                SELECT r.id, r.menu_item_id, r.produto_id, r.qtd_por_item, p.nome AS produto_nome
                FROM receitas r
                JOIN produtos p ON p.id = r.produto_id
                WHERE r.menu_item_id IN ({placeholders})
                """,
                ids,
            )
        for row in cur.fetchall():
            receitas.setdefault(row["menu_item_id"], []).append(row)

    cur.close()
    conn.close()
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

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # valida dono do item
    cur.execute("SELECT id FROM menu_itens WHERE id=%s AND usuario_id=%s", (item_id, uid))
    dono = cur.fetchone()
    if not dono:
        cur.close(); conn.close()
        flash("Item não encontrado.")
        return redirect(url_for("restaurant_bp.menu"))

    try:
        cur.execute(
            "INSERT INTO receitas (menu_item_id, produto_id, qtd_por_item) VALUES (%s,%s,%s)",
            (item_id, produto_id, float(qtd)),
        )
        conn.commit()
        flash("Ingrediente adicionado à receita.")
    except Exception as e:
        conn.rollback()
        flash("Falha ao adicionar ingrediente.")
        print("menu_receita_add ERR:", e)
    finally:
        cur.close(); conn.close()

    return redirect(url_for("restaurant_bp.menu"))

@restaurant_bp.route("/menu/receita/del/<int:receita_id>", methods=["POST"])
def menu_receita_del(receita_id: int):
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # valida se a receita é do usuário
    cur.execute(
        """
        SELECT r.id
        FROM receitas r
        JOIN menu_itens m ON m.id = r.menu_item_id
        WHERE r.id=%s AND m.usuario_id=%s
        """,
        (receita_id, uid),
    )
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        flash("Receita não encontrada.")
        return redirect(url_for("restaurant_bp.menu"))

    try:
        cur.execute("DELETE FROM receitas WHERE id=%s", (receita_id,))
        conn.commit()
        flash("Ingrediente removido.")
    except Exception as e:
        conn.rollback()
        flash("Falha ao remover ingrediente.")
        print("menu_receita_del ERR:", e)
    finally:
        cur.close(); conn.close()

    return redirect(url_for("restaurant_bp.menu"))

# ----------------------------------------------------
# REGISTRAR VENDA (a partir do menu + expansão receita)
# ----------------------------------------------------
@restaurant_bp.route("/registrar_venda_menu", methods=["GET", "POST"])
def registrar_venda_menu():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        menu_item_id = request.form.get("menu_item_id")
        qtd = int(float(request.form.get("quantidade") or 0))
        data_venda = request.form.get("data_venda")

        if not (menu_item_id and qtd > 0 and data_venda):
            flash("Preencha item, quantidade (>0) e data.")
            cur.close(); conn.close()
            return redirect(url_for("restaurant_bp.registrar_venda_menu"))

        # pega receita do item pertencente ao usuário
        cur.execute(
            """
            SELECT r.produto_id, r.qtd_por_item, p.preco_venda
            FROM receitas r
            JOIN produtos p ON p.id = r.produto_id
            JOIN menu_itens m ON m.id = r.menu_item_id
            WHERE r.menu_item_id=%s AND m.usuario_id=%s
            """,
            (menu_item_id, uid),
        )
        receita = cur.fetchall()
        if not receita:
            flash("Este item de menu não tem receita cadastrada.")
            cur.close(); conn.close()
            return redirect(url_for("restaurant_bp.registrar_venda_menu"))

        try:
            # cria venda
            cur.execute("INSERT INTO vendas (usuario_id, data) VALUES (%s,%s)", (uid, data_venda))
            venda_id = cur.lastrowid

            # expande receita -> itens_venda por produto
            for r in receita:
                produto_id = r["produto_id"]
                qtd_total = int(round(float(r["qtd_por_item"]) * qtd))  # garante INT
                preco_unit = float(r["preco_venda"])
                cur.execute(
                    """
                    INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (venda_id, produto_id, qtd_total, preco_unit),
                )

            conn.commit()
            flash("Venda registrada a partir do menu!")
        except Exception as e:
            conn.rollback()
            flash("Falha ao registrar venda.")
            print("registrar_venda_menu ERR:", e)
        finally:
            cur.close(); conn.close()

        return redirect(url_for("restaurant_bp.registrar_venda_menu"))

    # GET -> carrega itens do menu
    cur.execute("SELECT id, nome, preco FROM menu_itens WHERE usuario_id=%s ORDER BY nome", (uid,))
    itens = cur.fetchall()
    cur.close(); conn.close()
    return render_template("registrar_venda_menu.html", itens=itens)

# ---------------------------------------
# INGREDIENTES – CRUD simples + listagem
# ---------------------------------------
@restaurant_bp.route("/ingredientes", methods=["GET", "POST"])
def ingredientes():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        f = request.form
        try:
            cur.execute(
                """
                INSERT INTO ingredientes
                (usuario_id, nome, unidade, custo, perecivel, estoque_atual, estoque_minimo)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    uid,
                    f.get("nome"),
                    f.get("unidade") or None,
                    float(f.get("custo") or 0),
                    int(f.get("perecivel") or 0),
                    int(float(f.get("estoque_atual") or 0)),
                    int(float(f.get("estoque_minimo") or 0)),
                ),
            )
            conn.commit()
            flash("Ingrediente salvo!")
        except Exception as e:
            conn.rollback()
            flash("Erro ao salvar ingrediente.")
            print("ingredientes:insert ERR:", e)

    cur.execute(
        """
        SELECT id, nome, unidade, custo, perecivel, estoque_atual, estoque_minimo
        FROM ingredientes
        WHERE usuario_id=%s
        ORDER BY nome
        """,
        (uid,),
    )
    lista = cur.fetchall()
    cur.close(); conn.close()
    return render_template("ingredientes.html", ingredientes=lista)

# -------------------------------------------------
# LISTA DE COMPRAS – sugestão simples e funcional
# -------------------------------------------------
@restaurant_bp.route("/lista_compras")
def lista_compras():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    margem = max(0, min(100, int(request.args.get("margem", 20))))
    horizonte = max(1, min(30, int(request.args.get("horizonte", 7))))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # pega ingredientes atuais
    cur.execute(
        """
        SELECT id, nome, unidade, custo, estoque_atual, estoque_minimo
        FROM ingredientes
        WHERE usuario_id=%s
        ORDER BY nome
        """,
        (uid,),
    )
    ing = cur.fetchall()

    # Heurística simples: alvo = estoque_minimo * (horizonte/7) * (1+margem)
    fator = (horizonte / 7.0) * (1.0 + margem / 100.0)
    itens, total = [], 0.0
    for i in ing:
        alvo = int(round((i["estoque_minimo"] or 0) * fator))
        sugerido = max(0, alvo - int(i["estoque_atual"] or 0))
        if sugerido > 0:
            custo_estimado = float(i["custo"] or 0) * sugerido
            total += custo_estimado
            itens.append({
                "nome": i["nome"],
                "unidade": i["unidade"],
                "sugerido": sugerido,
                "custo": i["custo"],
                "custo_estimado": custo_estimado,
            })

    cur.close(); conn.close()
    return render_template("lista_compras.html", itens=itens, total=total, margem=margem, horizonte=horizonte)

# -------------------------------------------------
# RELATÓRIOS (Ingredientes) – KPIs e consumo básico
# -------------------------------------------------
@restaurant_bp.route("/relatorios")
def relatorios():
    if not _require_login():
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # KPIs de vendas (últimas 4 semanas)
    dt_ini = (datetime.utcnow() - timedelta(days=28)).strftime("%Y-%m-%d 00:00:00")
    cur.execute(
        """
        SELECT COUNT(DISTINCT v.id) AS total_vendas,
               COALESCE(SUM(iv.quantidade * iv.preco_unitario),0) AS receita
        FROM vendas v
        LEFT JOIN itens_venda iv ON iv.venda_id = v.id
        WHERE v.usuario_id=%s AND v.data >= %s
        """,
        (uid, dt_ini),
    )
    kpi = cur.fetchone() or {"total_vendas": 0, "receita": 0.0}

    # Consumo por ingrediente (estimado):
    # sem vínculo direto produto->ingrediente no seu schema atual, usamos proxy:
    # se estoque_atual < estoque_minimo, consideramos uso_total = (estoque_minimo - estoque_atual) + 10% buffer
    cur.execute(
        """
        SELECT nome, unidade, custo, estoque_atual, estoque_minimo
        FROM ingredientes
        WHERE usuario_id=%s
        ORDER BY nome
        """,
        (uid,),
    )
    consumo = []
    for row in cur.fetchall():
        falta = max(0, (row["estoque_minimo"] or 0) - (row["estoque_atual"] or 0))
        uso = int(round(falta * 1.1))
        consumo.append({
            "nome": row["nome"],
            "unidade": row["unidade"],
            "uso_total": uso,
            "custo": row["custo"],
            "custo_total": float(row["custo"] or 0) * uso
        })

    cur.close(); conn.close()
    return render_template("relatorios.html", kpi=kpi, consumo=consumo)
