from flask import Blueprint, request, render_template, session, redirect, url_for
from tcc_app.db import get_db_connection

compras_bp = Blueprint('compras_bp', __name__, url_prefix='/compras')

def _uid():
    return session.get('usuario_id')

@compras_bp.route('/lista', methods=['GET'])
def lista_compras():
    if not _uid():
        return redirect(url_for('auth_bp.login'))
    uid = _uid()

    margem = float(request.args.get('margem', '0.20'))   # 20% padrão
    semanas = int(request.args.get('semanas', '1'))      # horizonte (semanas)

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)

    # 1) previsão simples por item_menu: média das últimas 4 semanas (por semana)
    cur.execute("""
      SELECT im.id AS item_id, im.nome, COALESCE(SUM(vm.qtd),0) AS qtd_4w
      FROM itens_menu im
      LEFT JOIN vendas_menu vm ON vm.item_id = im.id AND vm.user_id = im.user_id
      WHERE im.user_id = %s AND (vm.data IS NULL OR vm.data >= (CURDATE() - INTERVAL 28 DAY))
      GROUP BY im.id
    """, (uid,))
    rows = cur.fetchall()
    prev = {r['item_id']: (float(r['qtd_4w'])/4.0) * semanas for r in rows}

    # 2) converte item -> ingrediente via receita
    cur.execute("""
      SELECT r.item_id, r.ingrediente_id, r.qtd_por_item,
             i.nome AS ing_nome, i.unidade, i.estoque_atual, i.custo_unitario
      FROM receita r
      JOIN ingredientes i ON i.id = r.ingrediente_id
      WHERE r.user_id = %s
    """, (uid,))
    comp = cur.fetchall()

    demanda = {}
    meta = {}
    for r in comp:
        uso = prev.get(r['item_id'], 0.0) * float(r['qtd_por_item'])
        ing_id = r['ingrediente_id']
        demanda[ing_id] = demanda.get(ing_id, 0.0) + uso
        meta[ing_id] = {
            "nome": r['ing_nome'],
            "unidade": r['unidade'],
            "estoque_atual": float(r['estoque_atual'] or 0.0),
            "custo_unitario": float(r['custo_unitario'] or 0.0),
        }

    compras = []
    for ing_id, dem in demanda.items():
        estoque = meta[ing_id]["estoque_atual"]
        neces = (dem - estoque) * (1 + margem)
        if neces > 0:
            custo_est = neces * meta[ing_id]["custo_unitario"]
            compras.append({
                "id": ing_id,
                "nome": meta[ing_id]["nome"],
                "unidade": meta[ing_id]["unidade"],
                "necessario": round(neces, 2),
                "custo_estimado": round(custo_est, 2)
            })

    total_itens = len(compras)
    total_custo = round(sum(x["custo_estimado"] for x in compras), 2)

    cur.close(); conn.close()
    return render_template('lista_compras.html',
                           compras=compras, margem=margem, semanas=semanas,
                           total_itens=total_itens, total_custo=total_custo)
