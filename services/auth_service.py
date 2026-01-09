from passlib.hash import bcrypt

from db.db import db


class AuthService:
    def verify_credentials(self, username: str, password: str) -> dict | None:
        user = db.query_one("SELECT * FROM users WHERE username = ?", (username,))
        if not user:
            return None
        if not bcrypt.verify(password, user["password_hash"]):
            return None
        return user

    def create_user(self, username: str, password: str, role: str) -> int:
        password_hash = bcrypt.hash(password)
        return db.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, db.now()),
        )

    def update_password(self, user_id: int, password: str) -> None:
        password_hash = bcrypt.hash(password)
        db.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?",
            (password_hash, user_id),
        )
