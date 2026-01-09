from db.db import db


class PetService:
    def create_pet(self, data: dict, user_id: int) -> int:
        pet_id = db.execute(
            "INSERT INTO pets (name, dob, breed, coat_color, eye_color, owner_phone, photo_path, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                data["name"],
                data["dob"],
                data["breed"],
                data["coat_color"],
                data["eye_color"],
                data["owner_phone"],
                data.get("photo_path"),
                db.now(),
            ),
        )
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "create", "pet", pet_id, db.now()),
        )
        return pet_id

    def update_pet(self, pet_id: int, data: dict, user_id: int) -> None:
        db.execute(
            "UPDATE pets SET name=?, dob=?, breed=?, coat_color=?, eye_color=?, owner_phone=?, photo_path=? "
            "WHERE pet_id=?",
            (
                data["name"],
                data["dob"],
                data["breed"],
                data["coat_color"],
                data["eye_color"],
                data["owner_phone"],
                data.get("photo_path"),
                pet_id,
            ),
        )
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "update", "pet", pet_id, db.now()),
        )

    def delete_pet(self, pet_id: int, user_id: int) -> None:
        db.execute("DELETE FROM pets WHERE pet_id = ?", (pet_id,))
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, "delete", "pet", pet_id, db.now()),
        )

    def list_pets(self, search: str | None = None) -> list[dict]:
        if search:
            return db.query_all(
                "SELECT * FROM pets WHERE name LIKE ? ORDER BY name",
                (f"%{search}%",),
            )
        return db.query_all("SELECT * FROM pets ORDER BY name")

    def get_pet(self, pet_id: int) -> dict | None:
        return db.query_one("SELECT * FROM pets WHERE pet_id = ?", (pet_id,))
