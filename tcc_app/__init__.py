from flask import Flask, request, redirect, url_for, session
from flask_login import LoginManager
from tcc_app.models import db, User

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from tcc_app.routes.auth_routes import auth_bp
    from tcc_app.routes.main_routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.before_request
    def require_login():
        allowed_routes = ['auth.login', 'static']
        if not session.get('usuario') and request.endpoint not in allowed_routes:
            return redirect(url_for('auth.login'))

    return app
