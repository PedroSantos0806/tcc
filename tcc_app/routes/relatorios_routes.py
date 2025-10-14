from flask import Blueprint, render_template, session, redirect, url_for
from tcc_app.db import get_db_connection

relatorios_bp = Blueprint('relatorios_bp', __name__, url_prefix='/relatorios')

def _uid(): 
    return session.get('usuario_id')

@relatorios_bp.route('/', methods=['GET'])
def relatorios_home():
    if not _uid():
        return redirect(url_for('auth_bp.login'))
    uid = _uid()

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    cur.execute("""
      SELECT i.nome, i.unidade,
             SUM(vm.qtd * r.qtd_por_item) AS uso_total,
             SUM(vm.qtd * r.qtd_por_item * i.custo_unitario) AS custo_total
      FROM vendas_menu vm
      JOIN receita r ON r.item_id = vm.item_id AND r.user_id = vm.user_id
      JOIN ingredientes i ON i.id = r.ingrediente_id AND i.user_id = vm.user_id
      WHERE vm.user_id = %s AND vm.data >= (CURDATE() - INTERVAL 28 DAY)
      GROUP BY i.id
      ORDER BY custo_total DESC
    """, (uid,))
    rows = cur.fetchall()
    cur.close(); conn.close()

    return render_template('relatorios.html', rows=rows)
