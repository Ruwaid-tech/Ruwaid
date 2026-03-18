from datetime import datetime

from app import db
from app.models import User, UserStatus
from app.security import generate_confirmation_token


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def test_registration_creates_inactive_user_pending_approval_and_sends_confirmation_email(client, app, outbox):
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

    messages = outbox()
    assert len(messages) == 1
    assert messages[0]["to"] == "new@example.com"
    assert "Confirm your Storage Access Manager account" == messages[0]["subject"]
    assert "/confirm/" in messages[0]["text_body"]


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


def test_admin_approval_activates_user_assigns_pin_and_emails_it(client, app, admin_user, outbox):
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
        user = db.session.get(User, user_id)
        assert user.status == UserStatus.ACTIVE
        assert user.pin_hash is not None

    messages = outbox()
    assert len(messages) == 1
    assert messages[0]["to"] == "approve@example.com"
    assert messages[0]["subject"] == "Your Storage Access Manager PIN code"
    assert "Your PIN code is:" in messages[0]["text_body"]
    assert "approve@example.com" not in messages[0]["text_body"]
