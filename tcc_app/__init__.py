import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    # -----------------------------
    # Filtros Jinja (PT-BR)
    # -----------------------------
    def _fmt_int(v):
        try:
            return f"{int(round(float(v)))}"
        except Exception:
            return "0"

    def _fmt_money(v):
        try:
            n = float(v)
        except Exception:
            n = 0.0
        s = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"

    app.jinja_env.filters["intbr"] = _fmt_int     # {{ valor|intbr }}
    app.jinja_env.filters["moneybr"] = _fmt_money # {{ valor|moneybr }}

    # DB teardown
    from .db import init_app as init_db
    init_db(app)

    # Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Blueprint do restaurante (Menu/Ingredientes/Compras/Relatórios)
    from .routes.restaurant_routes import restaurant_bp
    app.register_blueprint(restaurant_bp)

    # Health check
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
