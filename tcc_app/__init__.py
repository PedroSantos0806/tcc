from flask import Flask, request, redirect, url_for, session
from os import getenv
from dotenv import load_dotenv
from tcc_app.db import close_db_connection

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = getenv('SECRET_KEY', 'chave-padrao')

    app.config['DB_CONFIG'] = {
        'host': getenv('DB_HOST'),
        'user': getenv('DB_USER'),
        'password': getenv('DB_PASSWORD'),
        'database': getenv('DB_NAME'),
        'port': int(getenv('DB_PORT', 3306))
    }

    from tcc_app.routes.auth_routes import auth_bp
    from tcc_app.routes.main_routes import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)

    @app.before_request
    def require_login():
        allowed = ['auth_bp.login', 'auth_bp.cadastro', 'static']
        if request.endpoint not in allowed and 'usuario_id' not in session:
            return redirect(url_for('auth_bp.login'))

    app.teardown_appcontext(close_db_connection)

    return app
