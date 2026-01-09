from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Session:
    user: dict | None = None
    last_activity: datetime = field(default_factory=datetime.utcnow)

    def is_authenticated(self) -> bool:
        return self.user is not None

    def update_activity(self) -> None:
        self.last_activity = datetime.utcnow()

    def clear(self) -> None:
        self.user = None
        self.update_activity()
