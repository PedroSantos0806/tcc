import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    # registra teardown do DB
    from .db import init_app as init_db
    init_db(app)

    # importa blueprints DA PASTA routes/
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    return app