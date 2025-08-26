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

        # >>> muito importante para Render: falhar rápido se não conectar
        connection_timeout=5,

        # pool leve (opcional; se preferir, comente as 2 linhas abaixo)
        pool_name="tcc_pool",
        pool_size=2,
    )

    # SSL opcional (se o host exigir)
    ssl_on = os.getenv("DB_SSL", "0").lower() in ("1", "true", "yes")
    if ssl_on:
        ssl_ca = os.getenv("DB_SSL_CA_PATH", os.path.join(os.path.dirname(__file__), "certs", "DigiCertGlobalRootCA.pem"))
        if os.path.exists(ssl_ca):
            conf["ssl_ca"] = ssl_ca
    return conf

def get_db_connection():
    """Conexão avulsa para operações pontuais."""
    return mysql.connector.connect(**_db_conf())

def get_db():
    """Conexão reaproveitada por request."""
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

# alias pra compatibilidade antiga
def close_db_connection(e=None):
    return close_db(e)

def init_app(app):
    app.teardown_appcontext(close_db)
