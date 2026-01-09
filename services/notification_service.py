from datetime import datetime, timedelta

from db.db import db


class NotificationService:
    def due_schedules(self) -> list[dict]:
        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        db.execute(
            "UPDATE schedules SET status = 'due' WHERE status = 'snoozed' AND snoozed_until <= ?",
            (now,),
        )
        return db.query_all(
            "SELECT schedules.*, pets.name AS pet_name FROM schedules "
            "JOIN pets ON schedules.pet_id = pets.pet_id "
            "WHERE status = 'due' AND due_datetime <= ? ORDER BY due_datetime",
            (now,),
        )

    def upcoming_schedules(self) -> list[dict]:
        return db.query_all(
            "SELECT schedules.*, pets.name AS pet_name FROM schedules "
            "JOIN pets ON schedules.pet_id = pets.pet_id "
            "WHERE status IN ('due','snoozed') ORDER BY due_datetime",
        )

    def mark_done(self, schedule_id: int, user_id: int) -> None:
        db.execute(
            "UPDATE schedules SET status = 'done', done_at = ?, done_by = ? WHERE schedule_id = ?",
            (db.now(), user_id, schedule_id),
        )
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "complete", "schedule", schedule_id, db.now()),
        )

    def snooze(self, schedule_id: int, minutes: int) -> None:
        snoozed_until = (datetime.utcnow() + timedelta(minutes=minutes)).isoformat(
            sep=" ", timespec="seconds"
        )
        db.execute(
            "UPDATE schedules SET status = 'snoozed', snoozed_until = ? WHERE schedule_id = ?",
            (snoozed_until, schedule_id),
        )
