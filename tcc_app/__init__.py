from flask import Flask, request, redirect, url_for, session
from tcc_app.config import Config
from tcc_app.db import close_db_connection

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Carrega configurações do config.py

    from tcc_app.routes.auth_routes import auth_bp
    from tcc_app.routes.main_routes import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)

    # Verificação de login para rotas protegidas
    @app.before_request
    def require_login():
        allowed = ['auth_bp.login', 'auth_bp.cadastro', 'static']
        if request.endpoint not in allowed and 'usuario_id' not in session:
            return redirect(url_for('auth_bp.login'))

    # Fecha conexão com banco ao encerrar a requisição
    app.teardown_appcontext(close_db_connection)

    return app
