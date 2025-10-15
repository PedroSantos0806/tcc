import os
from flask import Flask
from dotenv import load_dotenv

# ---- Filtros Jinja (usados em vários templates) ----
def _fmt_int(v):
    try:
        return f"{int(round(float(v or 0))):,}".replace(",", ".")
    except Exception:
        return "0"

def _fmt_money(v):
    try:
        return "R$ " + f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def _fmt_date(dt):
    try:
        from datetime import datetime, date
        if isinstance(dt, (datetime, date)):
            return dt.strftime("%d/%m/%Y")
        s = str(dt)[:10]
        return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
    except Exception:
        return str(dt)

def create_app():
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    # DB teardown
    from .db import init_app as init_db
    init_db(app)

    # registra filtros
    app.jinja_env.filters["fmt_int"] = _fmt_int
    app.jinja_env.filters["fmt_money"] = _fmt_money
    app.jinja_env.filters["fmt_date"] = _fmt_date

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
