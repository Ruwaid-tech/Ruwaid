import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta, timezone

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User, UserRole, UserStatus


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret",
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = User(
            email="admin@test.com",
            password_hash=generate_password_hash("password123"),
            status=UserStatus.ACTIVE,
            email_confirmed_at=datetime.utcnow(),
            role=UserRole.ADMIN,
            role_expires_at=datetime.utcnow() + timedelta(days=1),
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def normal_user(app):
    with app.app_context():
        user = User(
            email="user@test.com",
            password_hash=generate_password_hash("password123"),
            status=UserStatus.ACTIVE,
            email_confirmed_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()
        return user
