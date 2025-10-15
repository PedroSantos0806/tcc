from tcc_app.db import get_db_connection

def obter_usuario_por_email(email):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    cursor.close()
    return usuario

def inserir_usuario(nome, email, senha):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, senha))
    db.commit()
    cursor.close()

def obter_usuario_por_id(usuario_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()
    return usuario

def obter_estoque_com_vendas(usuario_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*,
               GREATEST(p.quantidade - COALESCE((
                   SELECT SUM(iv.quantidade)
                   FROM itens_venda iv
                   JOIN vendas v ON v.id = iv.venda_id
                   WHERE iv.produto_id = p.id AND v.usuario_id = %s
               ), 0), 0) AS quantidade_atual
        FROM produtos p
        WHERE p.usuario_id = %s
    """, (usuario_id, usuario_id))
    produtos = cursor.fetchall()
    cursor.close()
    return produtos
