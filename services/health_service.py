from db.db import db


class HealthService:
    def add_record(self, data: dict, user_id: int) -> int:
        record_id = db.execute(
            "INSERT INTO health_records (pet_id, type, date, title, notes, dosage, created_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data["pet_id"],
                data["type"],
                data["date"],
                data["title"],
                data.get("notes"),
                data.get("dosage"),
                user_id,
                db.now(),
            ),
        )
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "create", "health_record", record_id, db.now()),
        )
        return record_id

    def list_records(self, pet_id: int, record_type: str | None = None) -> list[dict]:
        if record_type:
            return db.query_all(
                "SELECT health_records.*, users.username AS created_by_name FROM health_records "
                "LEFT JOIN users ON health_records.created_by = users.user_id "
                "WHERE pet_id = ? AND type = ? ORDER BY date DESC",
                (pet_id, record_type),
            )
        return db.query_all(
            "SELECT health_records.*, users.username AS created_by_name FROM health_records "
            "LEFT JOIN users ON health_records.created_by = users.user_id "
            "WHERE pet_id = ? ORDER BY date DESC",
            (pet_id,),
        )

    def add_weight(self, pet_id: int, date: str, weight_kg: float, user_id: int) -> int:
        weight_id = db.execute(
            "INSERT INTO weight_logs (pet_id, date, weight_kg, created_at) VALUES (?, ?, ?, ?)",
            (pet_id, date, weight_kg, db.now()),
        )
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "create", "weight_log", weight_id, db.now()),
        )
        return weight_id

    def list_weights(self, pet_id: int) -> list[dict]:
        return db.query_all(
            "SELECT * FROM weight_logs WHERE pet_id = ? ORDER BY date ASC",
            (pet_id,),
        )

    def add_schedule(self, data: dict, user_id: int) -> int:
        schedule_id = db.execute(
            "INSERT INTO schedules (pet_id, event_type, title, due_datetime, repeat_rule, status) "
            "VALUES (?, ?, ?, ?, ?, 'due')",
            (
                data["pet_id"],
                data["event_type"],
                data["title"],
                data["due_datetime"],
                data.get("repeat_rule"),
            ),
        )
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "create", "schedule", schedule_id, db.now()),
        )
        return schedule_id
