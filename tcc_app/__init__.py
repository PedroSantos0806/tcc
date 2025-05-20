from flask import Flask
import mysql.connector

def create_app():
    app = Flask(__name__)
    
    # Configurações do banco de dados Azure (ajuste com seus dados reais)
    app.config['DB_CONFIG'] = {
        'host': 'SEU_HOST.mysql.database.azure.com',
        'user': 'SEU_USUARIO@SEU_HOST',
        'password': 'SUA_SENHA',
        'database': 'SEU_NOME_DO_BANCO',
        'port': 3306
    }

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

def get_db_connection(app):
    return mysql.connector.connect(**app.config['DB_CONFIG'])
