import os
from datetime import datetime, timedelta, timezone

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///storage_access.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "dev-salt")



def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth_bp
    from .main import main_bp
    from .admin import admin_bp
    from .errors import register_error_handlers

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    @app.cli.command("seed-admin")
    def seed_admin():
        from .models import User, UserStatus, UserRole
        from werkzeug.security import generate_password_hash

        email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
        password = os.environ.get("ADMIN_PASSWORD", "AdminPass123!")

        if User.query.filter_by(email=email).first():
            print(f"Admin user already exists: {email}")
            return

        admin = User(
            email=email,
            password_hash=generate_password_hash(password),
            status=UserStatus.ACTIVE,
            email_confirmed_at=datetime.utcnow(),
            role=UserRole.ADMIN,
            role_expires_at=datetime.utcnow() + timedelta(days=3650),
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin user {email} with password {password}")

    return app
