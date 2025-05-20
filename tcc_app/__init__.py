# tcc_app/__init__.py

from flask import Flask
from .routes.main_routes import main_bp
from .routes.auth_routes import auth_routes

def create_app():
    app = Flask(__name__)
    app.secret_key = 'admin123456'

    # Configurações do banco de dados Azure
    app.config['DB_CONFIG'] = {
        'host': 'servidortcc.mysql.database.azure.com',
        'user': 'banco_superuser',
        'password': 'admin1234#',
        'database': 'banco_tcc',
        'port': 3306
    }

    # Registrar os blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_routes)

    return app
