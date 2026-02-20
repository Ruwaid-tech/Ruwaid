from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from app import db
from app.models import AccessLog, AccessResult, User, UserRole, UserStatus


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def test_user_cannot_access_admin_or_other_history(client, app):
    with app.app_context():
        user1 = User(email="u1@test.com", password_hash=generate_password_hash("abc"), status=UserStatus.ACTIVE, email_confirmed_at=datetime.utcnow())
        user2 = User(email="u2@test.com", password_hash=generate_password_hash("abc"), status=UserStatus.ACTIVE, email_confirmed_at=datetime.utcnow())
        admin = User(
            email="a@test.com",
            password_hash=generate_password_hash("abc"),
            status=UserStatus.ACTIVE,
            email_confirmed_at=datetime.utcnow(),
            role=UserRole.ADMIN,
            role_expires_at=datetime.utcnow() + timedelta(days=1),
        )
        db.session.add_all([user1, user2, admin])
        db.session.commit()

        db.session.add(AccessLog(user_id=user2.user_id, result=AccessResult.DENY, reason="TEST"))
        db.session.commit()
        user2_id = user2.user_id

    login(client, "u1@test.com", "abc")
    admin_resp = client.get("/admin/dashboard")
    assert admin_resp.status_code == 403

    other_resp = client.get(f"/user/{user2_id}/history")
    assert other_resp.status_code == 403
