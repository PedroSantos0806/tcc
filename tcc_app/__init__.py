from flask import Flask, request, redirect, url_for, session
from os import getenv

def create_app():
    app = Flask(__name__)

    # Configurações sensíveis
    app.config['SECRET_KEY'] = getenv('SECRET_KEY', 'sua-chave-secreta-aqui')
    app.config['DB_CONFIG'] = {
        'host': getenv('MYSQL_HOST', 'localhost'),
        'user': getenv('MYSQL_USER', 'root'),
        'password': getenv('MYSQL_PASSWORD', 'senha'),
        'database': getenv('MYSQL_DB', 'banco'),
    }

    # Importa e registra Blueprints
    from tcc_app.routes.auth_routes import auth_bp
    from tcc_app.routes.main_routes import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')  # URLs: /auth/login, /auth/cadastro, etc.
    app.register_blueprint(main_bp)                      # URLs: /, /ver_previsao, etc.

    # Middleware de verificação de login
    @app.before_request
    def require_login():
        allowed_routes = ['auth_bp.login', 'auth_bp.cadastro', 'static']
        if request.endpoint and request.endpoint not in allowed_routes:
            if not session.get('usuario_id'):
                return redirect(url_for('auth_bp.login'))

    return app
