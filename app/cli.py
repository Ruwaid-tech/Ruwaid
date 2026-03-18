import os
from datetime import datetime, timedelta

import click
from werkzeug.security import generate_password_hash

from . import db
from .models import User, UserRole, UserStatus


def register_cli(app):
    @app.cli.command("seed-admin")
    def seed_admin():
        email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        password = os.getenv("ADMIN_PASSWORD", "AdminPass123!")

        existing = User.query.filter_by(email=email).first()
        if existing:
            click.echo(f"Admin user already exists: {email}")
            return

        admin = User(
            email=email,
            password_hash=generate_password_hash(password),
            status=UserStatus.ACTIVE,
            role=UserRole.ADMIN,
            role_expires_at=datetime.utcnow() + timedelta(days=3650),
            email_confirmed_at=datetime.utcnow(),
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Created admin {email} with password {password}")
