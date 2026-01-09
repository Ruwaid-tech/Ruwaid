from datetime import datetime, timedelta

from db import init_db
from services import AuthService, FeedingService, HealthService, PetService


def seed() -> None:
    init_db()
    auth = AuthService()
    pets = PetService()
    feeding = FeedingService()
    health = HealthService()

    admin_id = auth.create_user("admin", "password123", "Admin")
    pet_id = pets.create_pet(
        {
            "name": "Milo",
            "dob": "2020-04-10",
            "breed": "Tabby",
            "coat_color": "Brown",
            "eye_color": "Green",
            "owner_phone": "555-123-4567",
            "photo_path": None,
        },
        admin_id,
    )
    feeding.add_feeding(
        {
            "pet_id": pet_id,
            "scheduled_datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "food_type": "Wet food",
            "amount": 120,
            "unit": "g",
        },
        admin_id,
    )
    health.add_record(
        {
            "pet_id": pet_id,
            "type": "vaccination",
            "date": datetime.today().date().isoformat(),
            "title": "Rabies Shot",
            "notes": "Initial dose",
            "dosage": "1 ml",
        },
        admin_id,
    )
    health.add_weight(pet_id, datetime.today().date().isoformat(), 4.2, admin_id)
    health.add_schedule(
        {
            "pet_id": pet_id,
            "event_type": "vaccination",
            "title": "Rabies booster",
            "due_datetime": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M"),
            "repeat_rule": "annual",
        },
        admin_id,
    )


if __name__ == "__main__":
    seed()
