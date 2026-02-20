from datetime import datetime, timezone
from enum import Enum

from flask_login import UserMixin

from . import db


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class AccessResult(str, Enum):
    GRANT = "GRANT"
    DENY = "DENY"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.INACTIVE)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER)
    role_expires_at = db.Column(db.DateTime, nullable=True)
    pin_hash = db.Column(db.String(255), nullable=True)
    email_confirmed_at = db.Column(db.DateTime, nullable=True)
    failed_pin_attempts = db.Column(db.Integer, nullable=False, default=0)
    last_failed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow())

    logs = db.relationship("AccessLog", back_populates="user", lazy=True)
    access_windows = db.relationship("AccessWindow", back_populates="user", lazy=True, cascade="all, delete-orphan")

    def get_id(self):
        return str(self.user_id)

    @property
    def email_confirmed(self):
        return self.email_confirmed_at is not None

    def has_admin_access(self):
        if self.role != UserRole.ADMIN:
            return False
        if self.role_expires_at is None:
            return True
        expiry = self.role_expires_at
        if expiry.tzinfo is not None:
            expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)
        return expiry >= datetime.utcnow()


class AccessWindow(db.Model):
    __tablename__ = "access_windows"

    win_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User", back_populates="access_windows")


class AccessLog(db.Model):
    __tablename__ = "access_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow(), index=True)
    result = db.Column(db.Enum(AccessResult), nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)

    user = db.relationship("User", back_populates="logs")
