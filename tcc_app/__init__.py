# tcc_app/__init__.py
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

    # --- Filtros Jinja para formatação (resolve 276.000 -> 276 etc.) ---
    @app.template_filter("fmt_int")
    def fmt_int(val):
        try:
            return f"{int(round(float(val))) :d}"
        except Exception:
            return val

    @app.template_filter("fmt_money")
    def fmt_money(val):
        try:
            return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return f"{val}"

    # Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    from .routes.restaurant_routes import restaurant_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(restaurant_bp)

    # Health check
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
