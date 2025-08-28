import os
from dotenv import load_dotenv
import mysql.connector
from flask import g

load_dotenv()  # carrega .env da raiz

def get_db_connection():
    cfg = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_DATABASE", "banco_tcc"),
        "autocommit": False,
    }
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca and os.path.exists(ssl_ca):
        cfg["ssl_ca"] = ssl_ca
    return mysql.connector.connect(**cfg)

# Opcional: conexão por request (se você já usa get_db() em algum lugar)
def get_db():
    if "db_conn" not in g:
        g.db_conn = get_db_connection()
    return g.db_conn

def close_db(e=None):
    db = g.pop("db_conn", None)
    if db is not None:
        db.close()