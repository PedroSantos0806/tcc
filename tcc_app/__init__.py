import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    # DB teardown
    from .db import init_app as init_db
    init_db(app)

    # Blueprints existentes
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # >>> NOVOS BLUEPRINTS <<<
    from .routes.menu_routes import menu_bp
    from .routes.compras_routes import compras_bp
    from .routes.relatorios_routes import relatorios_bp
    app.register_blueprint(menu_bp)
    app.register_blueprint(compras_bp)
    app.register_blueprint(relatorios_bp)

    # Health check
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app