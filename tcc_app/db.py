import mysql.connector
import os
from flask import current_app, g

def get_db_connection():
    if 'db_conn' not in g:
        # Caminho para o certificado SSL
        ssl_ca_path = os.path.join(os.getcwd(), 'tcc_app', 'certs', 'DigiCertGlobalRootCA.pem')

        config = {
            'user': os.environ.get('DB_USER'),
            'password': os.environ.get('DB_PASSWORD'),
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME'),
            'port': int(os.environ.get('DB_PORT', 3306)),
            'ssl_ca': ssl_ca_path
        }

        g.db_conn = mysql.connector.connect(**config)

    return g.db_conn

def close_db_connection(e=None):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()
