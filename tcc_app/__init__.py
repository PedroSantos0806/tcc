import os
from flask import Flask
from dotenv import load_dotenv

from tcc_app.db import init_app as init_db
from tcc_app.auth_routes import auth_bp
from tcc_app.main_routes import main_bp

def create_app():
    load_dotenv()  # lê .env se existir (no Render use env vars)
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # SECRET_KEY para sessão (troque em produção via env)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    # DB teardown/fechamento
    init_db(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
