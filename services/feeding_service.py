from db.db import db


class FeedingService:
    def add_feeding(self, data: dict, user_id: int) -> int:
        feed_id = db.execute(
            "INSERT INTO feeding_logs (pet_id, scheduled_datetime, food_type, amount, unit, completed_at, "
            "completed_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data["pet_id"],
                data["scheduled_datetime"],
                data["food_type"],
                data["amount"],
                data["unit"],
                None,
                None,
                db.now(),
            ),
        )
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "create", "feeding_log", feed_id, db.now()),
        )
        return feed_id

    def list_feedings_for_day(self, pet_id: int, date: str) -> list[dict]:
        return db.query_all(
            "SELECT feeding_logs.*, users.username AS completed_by_name FROM feeding_logs "
            "LEFT JOIN users ON feeding_logs.completed_by = users.user_id "
            "WHERE pet_id = ? AND scheduled_datetime LIKE ? ORDER BY scheduled_datetime",
            (pet_id, f"{date}%"),
        )

    def list_recent_feedings(self, pet_id: int, limit: int = 10) -> list[dict]:
        return db.query_all(
            "SELECT feeding_logs.*, users.username AS completed_by_name FROM feeding_logs "
            "LEFT JOIN users ON feeding_logs.completed_by = users.user_id "
            "WHERE pet_id = ? ORDER BY scheduled_datetime DESC LIMIT ?",
            (pet_id, limit),
        )

    def complete_feeding(self, feed_id: int, user_id: int) -> None:
        db.execute(
            "UPDATE feeding_logs SET completed_at = ?, completed_by = ? WHERE feed_id = ?",
            (db.now(), user_id, feed_id),
        )
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "complete", "feeding_log", feed_id, db.now()),
        )

    def feeding_completion_rate(self, pet_id: int) -> float:
        total = db.query_one(
            "SELECT COUNT(*) AS total FROM feeding_logs WHERE pet_id = ?",
            (pet_id,),
        )["total"]
        if total == 0:
            return 0.0
        completed = db.query_one(
            "SELECT COUNT(*) AS total FROM feeding_logs WHERE pet_id = ? AND completed_at IS NOT NULL",
            (pet_id,),
        )["total"]
        return completed / total
