import os
from dotenv import load_dotenv
import mysql.connector
from flask import g

# Carrega .env localmente; em produção, usa variáveis do ambiente
load_dotenv()

def _mysql_cfg():
    db_name = os.getenv("DB_DATABASE") or os.getenv("DB_NAME") or "banco_tcc"
    cfg = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": db_name,
        "autocommit": False,
        "connection_timeout": 10,
        "raise_on_warnings": True,
    }
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca and os.path.exists(ssl_ca):
        cfg["ssl_ca"] = ssl_ca
    return cfg

def get_db_connection():
    return mysql.connector.connect(**_mysql_cfg())

def get_db():
    if "db_conn" not in g:
        g.db_conn = get_db_connection()
    return g.db_conn

def close_db(e=None):
    db = g.pop("db_conn", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

def init_app(app):
    app.teardown_appcontext(close_db)
