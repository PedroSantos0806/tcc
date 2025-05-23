from db import get_db

def obter_usuario_por_email(email):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    return cursor.fetchone()

def inserir_usuario(nome, email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, senha))
    db.commit()

def obter_usuario_por_id(usuario_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
    return cursor.fetchone()
