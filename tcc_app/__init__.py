from flask import Flask
from tcc_app.db import close_db_connection
from tcc_app.routes.auth_routes import auth_bp
from tcc_app.routes.main_routes import main_bp
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    # Registrar rotas
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Encerrar conexão com banco após request
    app.teardown_appcontext(close_db_connection)

    return app
