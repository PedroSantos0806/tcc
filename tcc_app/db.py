import mysql.connector
from flask import current_app

def get_db_connection():
    config = current_app.config['DB_CONFIG']
    return mysql.connector.connect(**config)
