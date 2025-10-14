from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from tcc_app.db import get_db_connection

menu_bp = Blueprint('menu_bp', __name__, url_prefix='/menu')

# Helpers
def _uid():
    return session.get('usuario_id')

def _ensure_login():
    if not _uid():
        return redirect(url_for('auth_bp.login'))

# ===================== INGREDIENTES =====================
@menu_bp.route('/ingredientes', methods=['GET', 'POST'])
def ingredientes():
    redir = _ensure_login()
    if redir: return redir
    uid = _uid()

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        f = request.form
        cur.execute("""
            INSERT INTO ingredientes
              (user_id, nome, unidade, custo_unitario, perecivel, estoque_atual, estoque_minimo, status)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s, 'OK')
        """, (
            uid,
            f['nome'],
            f['unidade'],
            float(f.get('custo_unitario') or 0),
            1 if f.get('perecivel') == '1' else 0,
            float(f.get('estoque_atual') or 0),
            float(f.get('estoque_minimo') or 0)
        ))
        conn.commit()
        flash('Ingrediente cadastrado com sucesso.')
        cur.close(); conn.close()
        return redirect(url_for('menu_bp.ingredientes'))

    cur.execute("SELECT * FROM ingredientes WHERE user_id=%s ORDER BY nome", (uid,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template('ingredientes.html', ingredientes=rows)

# ===================== ITENS DE MENU =====================
@menu_bp.route('/itens', methods=['GET', 'POST'])
def itens_menu():
    redir = _ensure_login()
    if redir: return redir
    uid = _uid()

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        f = request.form
        cur.execute("""
            INSERT INTO itens_menu (user_id, nome, categoria, preco_venda, ativo)
            VALUES (%s, %s, %s, %s, 1)
        """, (uid, f['nome'], (f.get('categoria') or None), float(f.get('preco_venda') or 0)))
        conn.commit()
        flash('Item de menu criado.')
        cur.close(); conn.close()
        return redirect(url_for('menu_bp.itens_menu'))

    cur.execute("SELECT * FROM itens_menu WHERE user_id=%s ORDER BY nome", (uid,))
    itens = cur.fetchall()
    cur.close(); conn.close()
    return render_template('menu.html', itens=itens)

# ===================== RECEITA DO ITEM =====================
@menu_bp.route('/receita/<int:item_id>', methods=['GET', 'POST'])
def receita_item(item_id):
    redir = _ensure_login()
    if redir: return redir
    uid = _uid()

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        f = request.form
        cur.execute("""
            INSERT INTO receita (user_id, item_id, ingrediente_id, qtd_por_item)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE qtd_por_item = VALUES(qtd_por_item)
        """, (uid, item_id, int(f['ingrediente_id']), float(f['qtd_por_item'])))
        conn.commit()
        flash('Ingrediente adicionado/atualizado na receita.')
        cur.close(); conn.close()
        return redirect(url_for('menu_bp.receita_item', item_id=item_id))

    # GET
    cur.execute("SELECT * FROM itens_menu WHERE id=%s AND user_id=%s", (item_id, uid))
    item = cur.fetchone()
    if not item:
        cur.close(); conn.close()
        flash('Item não encontrado.')
        return redirect(url_for('menu_bp.itens_menu'))

    cur.execute("SELECT * FROM ingredientes WHERE user_id=%s ORDER BY nome", (uid,))
    ingredientes = cur.fetchall()

    cur.execute("""
        SELECT r.*, i.nome AS ing_nome, i.unidade
        FROM receita r
        JOIN ingredientes i ON i.id = r.ingrediente_id
        WHERE r.user_id=%s AND r.item_id=%s
        ORDER BY ing_nome
    """, (uid, item_id))
    componentes = cur.fetchall()
    cur.close(); conn.close()

    return render_template('receita.html', item=item, ingredientes=ingredientes, componentes=componentes)

# ===================== REGISTRAR VENDA (MENU) =====================
@menu_bp.route('/registrar_venda', methods=['GET', 'POST'])
def registrar_venda_menu():
    redir = _ensure_login()
    if redir: return redir
    uid = _uid()

    conn = get_db_connection(); cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        item_id = int(request.form['item_id'])
        data = request.form['data']
        qtd = int(request.form['qtd'])

        # grava venda
        cur.execute("INSERT INTO vendas_menu (user_id, item_id, data, qtd) VALUES (%s, %s, %s, %s)",
                    (uid, item_id, data, qtd))

        # debita estoque por receita
        cur.execute("SELECT ingrediente_id, qtd_por_item FROM receita WHERE user_id=%s AND item_id=%s",
                    (uid, item_id))
        recs = cur.fetchall()
        for r in recs:
            saida = qtd * float(r['qtd_por_item'])
            cur.execute("""
                UPDATE ingredientes
                SET estoque_atual = GREATEST(0, estoque_atual - %s)
                WHERE user_id=%s AND id=%s
            """, (saida, uid, r['ingrediente_id']))
            # log opcional
            cur.execute("""
                INSERT INTO estoque_mov (user_id, ingrediente_id, tipo, qtd, observacao)
                VALUES (%s, %s, 'SAIDA', %s, %s)
            """, (uid, r['ingrediente_id'], saida, f"Venda item_menu {item_id}"))

        conn.commit()
        cur.close(); conn.close()
        flash('Venda registrada e estoque debitado.')
        return redirect(url_for('menu_bp.registrar_venda_menu'))

    # GET
    cur.execute("SELECT id, nome FROM itens_menu WHERE user_id=%s AND ativo=1 ORDER BY nome", (uid,))
    itens = cur.fetchall()
    cur.close(); conn.close()
    return render_template('registrar_venda_menu.html', itens=itens)
