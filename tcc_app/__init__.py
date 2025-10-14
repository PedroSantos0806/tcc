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

    # Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    # >>> ADIÇÃO: rotas do “Restaurante”
    from .routes.restaurant_routes import restaurant_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    # >>> registra também
    app.register_blueprint(restaurant_bp, url_prefix="")

    # Health check
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
