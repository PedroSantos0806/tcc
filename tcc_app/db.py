import os
import mysql.connector
from flask import g

def _db_conf():
    return dict(
        host=os.getenv("DB_HOST", "191.36.128.250"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Phlgbabi@10"),
        database=os.getenv("DB_NAME", "banco_tcc"),
        port=int(os.getenv("DB_PORT", "3306")),
        autocommit=False
    )

def get_db_connection():
    # conexão “nova” (use em operações pontuais)
    return mysql.connector.connect(**_db_conf())

def get_db():
    # conexão “por request” (reuse)
    if 'db' not in g:
        g.db = mysql.connector.connect(**_db_conf())
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

def init_app(app):
    app.teardown_appcontext(close_db)
