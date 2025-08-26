import os
import mysql.connector
from flask import g

def _db_conf():
    conf = dict(
        host=os.getenv("DB_HOST", "191.36.128.250"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Phlgbabi@10"),
        database=os.getenv("DB_NAME", "banco_tcc"),
        port=int(os.getenv("DB_PORT", "3306")),
        autocommit=False,
    )
    # SSL opcional (se o provedor exigir)
    ssl_ca = os.getenv("DB_SSL_CA_PATH", os.path.join(os.path.dirname(__file__), "certs", "DigiCertGlobalRootCA.pem"))
    if os.path.exists(ssl_ca) and os.getenv("DB_SSL", "0") in ("1", "true", "TRUE"):
        conf["ssl_ca"] = ssl_ca
    return conf

def get_db_connection():
    """Conexão avulsa: use em operações pontuais."""
    return mysql.connector.connect(**_db_conf())

def get_db():
    """Conexão reaproveitada por request (fica em g)."""
    if "db" not in g:
        g.db = mysql.connector.connect(**_db_conf())
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

# Alias para compatibilidade com imports antigos
def close_db_connection(e=None):
    return close_db(e)

def init_app(app):
    app.teardown_appcontext(close_db)
