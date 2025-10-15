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

    # ---- Filtros Jinja usados nos templates ----
    def fmt_int(v):
        try:
            return f"{int(round(float(v or 0))):,}".replace(",", ".")
        except:
            return "0"
    def fmt_money(v):
        try:
            return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"

    app.jinja_env.filters["fmt_int"] = fmt_int
    app.jinja_env.filters["fmt_money"] = fmt_money

    # Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    from .routes.restaurant_routes import restaurant_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(restaurant_bp, url_prefix="")

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
