from flask import Blueprint, render_template, session, redirect, url_for
from tcc_app.db import get_db_connection

relatorios_bp = Blueprint("relatorios_bp", __name__)

@relatorios_bp.route("/relatorios")
def relatorios():
    if "usuario_id" not in session:
        return redirect(url_for("auth_bp.login"))
    uid = session["usuario_id"]

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT 
          COUNT(DISTINCT v.id) AS total_vendas,
          COALESCE(SUM(iv.quantidade * iv.preco_unitario),0) AS receita,
          COALESCE(SUM(iv.quantidade * p.preco_custo),0) AS custo_total
        FROM vendas v
        LEFT JOIN itens_venda iv ON iv.venda_id = v.id
        LEFT JOIN produtos p ON p.id = iv.produto_id
        WHERE v.usuario_id = %s
    """, (uid,))
    row = cur.fetchone() or {"total_vendas":0, "receita":0.0, "custo_total":0.0}
    kpi = {
        "total_vendas": int(row["total_vendas"] or 0),
        "receita": float(row["receita"] or 0.0),
        "custo_total": float(row["custo_total"] or 0.0),
    }

    cur.execute("""
        SELECT p.nome, 'un' AS unidade,
               COALESCE(SUM(iv.quantidade),0) AS uso_total,
               COALESCE(SUM(iv.quantidade * p.preco_custo),0) AS custo_total
        FROM itens_venda iv
        JOIN vendas v   ON v.id = iv.venda_id
        JOIN produtos p ON p.id = iv.produto_id
        WHERE v.usuario_id = %s
          AND v.data >= (CURRENT_DATE - INTERVAL 28 DAY)
        GROUP BY p.id
        ORDER BY uso_total DESC, p.nome
    """, (uid,))
    consumo = cur.fetchall() or []

    cur.close(); conn.close()
    return render_template("relatorios.html", kpi=kpi, consumo=consumo)
