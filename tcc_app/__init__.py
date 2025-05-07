# tcc_app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = 'sua_chave_secreta'

    from tcc_app.routes.auth_routes import auth_bp
    from tcc_app.routes.main_routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
