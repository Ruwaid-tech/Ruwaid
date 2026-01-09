from __future__ import annotations

import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

from config import APP_TITLE, AUTO_LOGOUT_MINUTES
from db import init_db
from services import (
    AuthService,
    AuditService,
    FeedingService,
    HealthService,
    NotificationService,
    PetService,
    ScoreService,
    UserService,
)
from app.session import Session
from app.views.dashboard_view import DashboardView
from app.views.feeding_logs_view import FeedingLogsView
from app.views.health_records_view import HealthRecordsView
from app.views.login_view import LoginView
from app.views.notifications_view import NotificationsView
from app.views.pet_profile_view import PetProfileView
from app.views.settings_view import SettingsView


class MainApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x720")
        self.minsize(1000, 650)
        self.session = Session()
        init_db()

        self.services = {
            "auth": AuthService(),
            "user": UserService(),
            "pets": PetService(),
            "feeding": FeedingService(),
            "health": HealthService(),
            "notifications": NotificationService(),
            "score": ScoreService(),
            "audit": AuditService(),
        }

        self.active_frame: tk.Frame | None = None
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.seen_reminders: set[int] = set()

        self.bind_all("<Any-KeyPress>", self._register_activity)
        self.bind_all("<Any-Button>", self._register_activity)

        self.show_login()
        self.after(60000, self._check_inactivity)
        self.after(60000, self._check_reminders)

    def _register_activity(self, _event) -> None:
        self.session.update_activity()

    def _check_inactivity(self) -> None:
        if self.session.is_authenticated():
            if datetime.utcnow() - self.session.last_activity > timedelta(minutes=AUTO_LOGOUT_MINUTES):
                messagebox.showinfo("Session Timeout", "You were logged out due to inactivity.")
                self.logout()
        self.after(60000, self._check_inactivity)

    def _check_reminders(self) -> None:
        if self.session.is_authenticated():
            due = self.services["notifications"].due_schedules()
            new_items = [item for item in due if item["schedule_id"] not in self.seen_reminders]
            if new_items:
                titles = "\n".join(
                    f"{item['pet_name']} - {item['title']} ({item['event_type']})" for item in new_items
                )
                messagebox.showinfo("Reminders Due", f"The following reminders are due:\n{titles}")
                self.seen_reminders.update(item["schedule_id"] for item in new_items)
        self.after(60000, self._check_reminders)

    def show_login(self) -> None:
        if self.active_frame:
            self.active_frame.destroy()
        self.active_frame = LoginView(self.container, self)
        self.active_frame.pack(fill="both", expand=True)

    def show_shell(self, page: str = "dashboard") -> None:
        if self.active_frame:
            self.active_frame.destroy()
        frame_map = {
            "dashboard": DashboardView,
            "pets": PetProfileView,
            "feeding": FeedingLogsView,
            "health": HealthRecordsView,
            "notifications": NotificationsView,
            "settings": SettingsView,
        }
        view_class = frame_map.get(page, DashboardView)
        self.active_frame = view_class(self.container, self)
        self.active_frame.pack(fill="both", expand=True)

    def login(self, user: dict) -> None:
        self.session.user = user
        self.session.update_activity()
        self.show_shell("dashboard")

    def logout(self) -> None:
        self.session.clear()
        self.show_login()
