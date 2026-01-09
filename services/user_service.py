from db.db import db


class UserService:
    def list_users(self) -> list[dict]:
        return db.query_all("SELECT user_id, username, role, created_at FROM users ORDER BY username")

    def update_username(self, user_id: int, username: str) -> None:
        db.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
