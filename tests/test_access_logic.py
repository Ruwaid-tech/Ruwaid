from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from app import db
from app.models import AccessLog, AccessResult, AccessWindow, User, UserStatus
from app.security import process_access_attempt


def test_process_access_attempt_logic(app):
    now = datetime.utcnow()
    with app.app_context():
        user = User(
            email="logic@test.com",
            password_hash="x",
            status=UserStatus.INACTIVE,
            email_confirmed_at=now,
            pin_hash=generate_password_hash("123456"),
        )
        db.session.add(user)
        db.session.commit()
        uid = user.user_id

        ok, _ = process_access_attempt(uid, "123456", now)
        assert ok is False

        user.status = UserStatus.ACTIVE
        db.session.commit()

        ok, _ = process_access_attempt(uid, "badpin", now)
        assert ok is False

        window = AccessWindow(user_id=uid, start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2))
        db.session.add(window)
        db.session.commit()

        ok, _ = process_access_attempt(uid, "123456", now)
        assert ok is False

        inside = now + timedelta(hours=1, minutes=10)
        ok, _ = process_access_attempt(uid, "123456", inside)
        assert ok is True

        missing_ok, _ = process_access_attempt(999999, "123", now)
        assert missing_ok is False

        logs = AccessLog.query.order_by(AccessLog.log_id.asc()).all()
        assert len(logs) == 5
        assert [l.result for l in logs] == [
            AccessResult.DENY,
            AccessResult.DENY,
            AccessResult.DENY,
            AccessResult.GRANT,
            AccessResult.DENY,
        ]
