from datetime import datetime, timedelta, timezone

from app import db
from app.models import User, UserStatus
from app.security import generate_confirmation_token


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def test_registration_creates_inactive_user_pending_approval(client, app):
    client.post(
        "/register",
        data={"email": "new@example.com", "password": "password123", "confirm_password": "password123"},
        follow_redirects=True,
    )

    with app.app_context():
        user = User.query.filter_by(email="new@example.com").first()
        assert user is not None
        assert user.status == UserStatus.INACTIVE
        assert user.email_confirmed is False


def test_email_confirm_toggles_state(client, app):
    with app.app_context():
        user = User(email="confirm@example.com", password_hash="x", status=UserStatus.INACTIVE)
        db.session.add(user)
        db.session.commit()
        token = generate_confirmation_token(app, user.email)

    client.get(f"/confirm/{token}", follow_redirects=True)

    with app.app_context():
        user = User.query.filter_by(email="confirm@example.com").first()
        assert user.email_confirmed is True


def test_admin_approval_activates_user_and_assigns_pin(client, app, admin_user):
    with app.app_context():
        user = User(
            email="approve@example.com",
            password_hash="x",
            status=UserStatus.INACTIVE,
            email_confirmed_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.user_id

    login(client, "admin@test.com", "password123")
    client.post(f"/admin/users/{user_id}/approve", follow_redirects=True)

    with app.app_context():
        user = User.query.get(user_id)
        assert user.status == UserStatus.ACTIVE
        assert user.pin_hash is not None
