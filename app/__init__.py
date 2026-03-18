import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from .email_service import EmailService


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
email_service = EmailService()


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}



def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    default_outbox = Path(app.instance_path) / "dev_mailbox.json"
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///storage_access.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_TIME_LIMIT=None,
        MAIL_DELIVERY=os.getenv("MAIL_DELIVERY", "console_and_file"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", "no-reply@storage-access.local"),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", "25")),
        MAIL_USE_TLS=_env_flag("MAIL_USE_TLS", False),
        MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
        DEV_EMAIL_OUTBOX=os.getenv("DEV_EMAIL_OUTBOX", str(default_outbox)),
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    email_service.init_app(app)
    login_manager.login_view = "login"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import register_routes

    register_routes(app)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="You are not allowed to access that page."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template("error.html", code=500, message="Something went wrong. Please try again."), 500

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    with app.app_context():
        db.create_all()

    from .cli import register_cli

    register_cli(app)

    return app
