from db.db import db


class AuditService:
    def log(self, user_id: int, action: str, entity_type: str, entity_id: int) -> None:
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, entity_type, entity_id, db.now()),
        )

    def recent(self, limit: int = 10) -> list[dict]:
        return db.query_all(
            "SELECT audit_log.*, users.username FROM audit_log "
            "LEFT JOIN users ON audit_log.user_id = users.user_id "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
