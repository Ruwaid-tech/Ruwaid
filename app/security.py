import secrets
from datetime import datetime

from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import AccessLog, AccessResult, AccessWindow, User, UserStatus


def generate_confirmation_token(app, email):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="email-confirm")


def confirm_token(app, token, max_age=86400):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.loads(token, salt="email-confirm", max_age=max_age)


def generate_pin_code():
    return f"{secrets.randbelow(900000) + 100000}"


def hash_pin(pin):
    return generate_password_hash(pin)


def generate_unique_pin():
    existing_hashes = [row.pin_hash for row in User.query.filter(User.pin_hash.isnot(None)).all()]
    while True:
        candidate = generate_pin_code()
        if all(not check_password_hash(pin_hash, candidate) for pin_hash in existing_hashes):
            return candidate


def log_attempt(user_id, result, reason, ip_address, when):
    log = AccessLog(
        user_id=user_id,
        timestamp=when,
        result=result,
        reason=reason,
        ip_address=ip_address,
    )
    db.session.add(log)


def process_access_attempt(user_id, entered_code, current_time, ip_address=None):
    user = User.query.get(user_id)

    if not user:
        log_attempt(None, AccessResult.DENY, "USER_NOT_FOUND", ip_address, current_time)
        db.session.commit()
        return False, "User does not exist."

    if user.status != UserStatus.ACTIVE:
        log_attempt(user.user_id, AccessResult.DENY, "ACCOUNT_INACTIVE", ip_address, current_time)
        db.session.commit()
        return False, "Account is inactive."

    if not user.pin_hash or not check_password_hash(user.pin_hash, entered_code):
        user.failed_pin_attempts += 1
        user.last_failed_at = current_time
        log_attempt(user.user_id, AccessResult.DENY, "INVALID_PIN", ip_address, current_time)
        db.session.commit()
        return False, "Invalid PIN."

    window = (
        AccessWindow.query.filter_by(user_id=user.user_id)
        .filter(AccessWindow.start_time <= current_time, AccessWindow.end_time >= current_time)
        .first()
    )
    has_any_window = AccessWindow.query.filter_by(user_id=user.user_id).count() > 0
    if has_any_window and not window:
        log_attempt(user.user_id, AccessResult.DENY, "OUTSIDE_ACCESS_WINDOW", ip_address, current_time)
        db.session.commit()
        return False, "Outside permitted access window."

    log_attempt(user.user_id, AccessResult.GRANT, "ACCESS_GRANTED", ip_address, current_time)
    db.session.commit()
    return True, "Access granted."
