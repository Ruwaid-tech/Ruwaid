from statistics import pstdev

from services.feeding_service import FeedingService
from services.health_service import HealthService
from services.notification_service import NotificationService


class ScoreService:
    def __init__(self) -> None:
        self.feeding_service = FeedingService()
        self.health_service = HealthService()
        self.notification_service = NotificationService()

    def compute_score(self, pet_id: int) -> dict:
        weights = self.health_service.list_weights(pet_id)
        weight_values = [row["weight_kg"] for row in weights]
        weight_score = self._weight_score(weight_values)

        feeding_rate = self.feeding_service.feeding_completion_rate(pet_id)
        nutrition_score = int(feeding_rate * 100)

        exercise_records = self.health_service.list_records(pet_id, "exercise")
        exercise_score = min(100, len(exercise_records) * 10)

        schedules = self.notification_service.upcoming_schedules()
        due_count = len([s for s in schedules if s["pet_id"] == pet_id and s["status"] != "done"])
        medical_score = max(0, 100 - due_count * 10)

        total = int((weight_score + nutrition_score + exercise_score + medical_score) / 4)
        total = max(1, min(100, total))

        explanation = self._explanation(weight_score, nutrition_score, exercise_score, medical_score)

        return {
            "total": total,
            "components": {
                "Weight Trend": weight_score,
                "Nutrition": nutrition_score,
                "Exercise": exercise_score,
                "Medical": medical_score,
            },
            "explanation": explanation,
        }

    def _weight_score(self, weights: list[float]) -> int:
        if len(weights) < 2:
            return 70
        volatility = pstdev(weights)
        if volatility < 0.2:
            return 90
        if volatility < 0.5:
            return 75
        return 60

    def _explanation(self, weight: int, nutrition: int, exercise: int, medical: int) -> str:
        notes = []
        if weight < 70:
            notes.append("Weight trend shows volatility.")
        if nutrition < 70:
            notes.append("Feeding completion is inconsistent.")
        if exercise < 70:
            notes.append("Exercise logs are infrequent.")
        if medical < 70:
            notes.append("Pending medical items need attention.")
        if not notes:
            return "All signals look strong. Keep up the good work!"
        return " ".join(notes)
