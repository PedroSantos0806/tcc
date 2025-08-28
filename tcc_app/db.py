# tcc_app/db.py
import os
from dotenv import load_dotenv
import mysql.connector
from flask import g

# Carrega variáveis do .env da raiz
load_dotenv()

def get_db_connection():
    """Abre uma conexão nova com o MySQL usando as variáveis do .env."""
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

def get_db():
    """Retorna a conexão por request (reaproveita via flask.g)."""
    if "db_conn" not in g:
        g.db_conn = get_db_connection()
    return g.db_conn

def close_db(e=None):
    """Fecha a conexão atrelada ao request (se existir)."""
    db = g.pop("db_conn", None)
    if db is not None:
        db.close()

def init_app(app):
    """
    Integra com o Flask: registra o fechamento da conexão no teardown.
    Mantém compatibilidade com from .db import init_app em __init__.py
    """
    app.teardown_appcontext(close_db)
