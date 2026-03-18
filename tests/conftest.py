import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models import User, UserRole, UserStatus


@pytest.fixture
def app(tmp_path):
    outbox_path = tmp_path / "dev_mailbox.json"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret",
            "DEV_EMAIL_OUTBOX": str(outbox_path),
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
def outbox(app):
    def _read_messages():
        path = Path(app.config["DEV_EMAIL_OUTBOX"])
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    return _read_messages


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
