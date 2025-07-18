import mysql.connector
import os
from flask import g

def get_db_connection():
    """
    Retorna uma conexão direta ao banco (usado quando não está em contexto de app Flask).
    """
    if 'db_conn' not in g:
        config = {
            'user': os.environ.get('DB_USER'),
            'password': os.environ.get('DB_PASSWORD'),
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME'),
            'port': int(os.environ.get('DB_PORT', 3306)),
        }
        g.db_conn = mysql.connector.connect(**config)
    return g.db_conn

def get_db():
    """
    Retorna a conexão atual do Flask (mais comum em rotas).
    """
    return get_db_connection()

def close_db_connection(e=None):
    """
    Fecha a conexão do banco após o uso, automaticamente.
    """
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()
