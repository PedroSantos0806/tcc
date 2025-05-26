import mysql.connector
import os
from flask import current_app, g

def get_db_connection():
    if 'db_conn' not in g:
        config = {
            'user': os.environ.get('DB_USER') + '@servidortcc',  # concatena domínio do servidor
            'password': os.environ.get('DB_PASSWORD'),
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME'),
            'port': int(os.environ.get('DB_PORT', 3306))
        }

        g.db_conn = mysql.connector.connect(**config)

    return g.db_conn

def close_db_connection(e=None):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()
