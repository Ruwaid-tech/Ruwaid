import secrets
from datetime import datetime, timezone

from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from .models import AccessLog, AccessResult, AccessWindow, User, UserStatus
from . import db


def make_serializer(app):
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt=app.config["SECURITY_PASSWORD_SALT"])


def generate_confirmation_token(app, email):
    return make_serializer(app).dumps(email)


def confirm_token(app, token, expiration=3600 * 24):
    return make_serializer(app).loads(token, max_age=expiration)


def generate_pin():
    return f"{secrets.randbelow(1000000):06d}"


def log_attempt(user_id, result, reason, ip_address, ts):
    log = AccessLog(user_id=user_id, result=result, reason=reason, ip_address=ip_address, timestamp=to_utc_naive(ts))
    db.session.add(log)


def process_access_attempt(user_id, entered_code, current_time, ip_address=None):
    current_time = to_utc_naive(current_time)
    user = db.session.get(User, user_id) if user_id is not None else None

    if not user:
        log_attempt(None, AccessResult.DENY, "USER_NOT_FOUND", ip_address, current_time)
        db.session.commit()
        return False, "User not found"

    if user.status != UserStatus.ACTIVE or not user.email_confirmed:
        log_attempt(user.user_id, AccessResult.DENY, "USER_INACTIVE", ip_address, current_time)
        db.session.commit()
        return False, "Account is inactive"

    if not user.pin_hash or not check_password_hash(user.pin_hash, entered_code):
        user.failed_pin_attempts += 1
        user.last_failed_at = current_time
        log_attempt(user.user_id, AccessResult.DENY, "WRONG_PIN", ip_address, current_time)
        db.session.commit()
        return False, "Invalid PIN"

    active_window = (
        AccessWindow.query.filter(
            AccessWindow.user_id == user.user_id,
            AccessWindow.start_time <= current_time,
            AccessWindow.end_time >= current_time,
        )
        .order_by(AccessWindow.start_time.desc())
        .first()
    )
    has_any_window = AccessWindow.query.filter_by(user_id=user.user_id).count() > 0

    if has_any_window and not active_window:
        log_attempt(user.user_id, AccessResult.DENY, "OUTSIDE_ACCESS_WINDOW", ip_address, current_time)
        db.session.commit()
        return False, "Outside permitted access window"

    user.failed_pin_attempts = 0
    log_attempt(user.user_id, AccessResult.GRANT, "ACCESS_GRANTED", ip_address, current_time)
    db.session.commit()
    return True, "Access granted"




def to_utc_naive(dt):
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

def hash_pin(pin):
    return generate_password_hash(pin)


def mark_email_confirmed(user):
    user.email_confirmed_at = datetime.utcnow()
    db.session.commit()
