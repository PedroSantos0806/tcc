import mysql.connector
from flask import current_app, g

def get_db_connection():
    if 'db_conn' not in g:
        config = current_app.config['DB_CONFIG']
        g.db_conn = mysql.connector.connect(**config)
    return g.db_conn

def close_db_connection(e=None):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()
