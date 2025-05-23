from flask import Flask, request, redirect, url_for, session
from os import getenv

def create_app():
    app = Flask(__name__)
    
    # Configurações (pode ajustar conforme seu config.py)
    app.config['SECRET_KEY'] = getenv('SECRET_KEY', 'sua-chave-secreta-aqui')
    app.config['DB_CONFIG'] = {
        'host': getenv('MYSQL_HOST', 'seu-host-mysql'),
        'user': getenv('MYSQL_USER', 'seu-usuario'),
        'password': getenv('MYSQL_PASSWORD', 'sua-senha'),
        'database': getenv('MYSQL_DB', 'seu-banco'),
    }

    # Importa blueprints
    from tcc_app.routes.auth_routes import auth_bp
    from tcc_app.routes.main_routes import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Controla acesso, exige login para rotas protegidas
    @app.before_request
    def require_login():
        allowed_routes = ['auth.login', 'auth.register', 'static']
        # request.endpoint pode ser None (ex: favicon), então protege
        if request.endpoint and request.endpoint not in allowed_routes:
            if not session.get('usuario'):
                return redirect(url_for('auth.login'))
    
    return app
