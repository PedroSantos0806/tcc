# tcc_app/__init__.py
from flask import Flask
from .routes.main_routes import main_bp  # Importando o Blueprint main_bp
from .routes.auth_routes import auth_routes  # Importando o Blueprint auth_routes

def create_app():
    # Criando a instância do app Flask
    app = Flask(__name__)
    app.secret_key = 'secreta-chave-super-segura'  # Definindo a chave secreta para sessões

    # Registrando os Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_routes)

    return app
