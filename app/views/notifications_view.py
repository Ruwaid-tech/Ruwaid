from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from app.views.base_view import BaseView


class NotificationsView(BaseView):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, app, "Notifications")
        self.alerts_enabled = tk.BooleanVar(value=True)
        self.email_enabled = tk.BooleanVar(value=False)
        self._build_content()
        self._refresh()

    def _build_content(self) -> None:
        header = tk.Label(self.content, text="Notifications", font=("Helvetica", 18, "bold"), bg="#f6f7fb")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        settings = tk.Frame(self.content, bg="white", padx=20, pady=10)
        settings.pack(fill="x", padx=20, pady=10)
        tk.Checkbutton(settings, text="Enable app alerts", variable=self.alerts_enabled, bg="white").pack(
            anchor="w"
        )
        tk.Checkbutton(settings, text="Enable email alerts (stub)", variable=self.email_enabled, bg="white").pack(
            anchor="w"
        )

        self.listbox = tk.Listbox(self.content, height=12)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=10)

        controls = tk.Frame(self.content, bg="#f6f7fb")
        controls.pack(fill="x", padx=20)
        tk.Button(controls, text="Mark Done", command=self._mark_done).pack(side="left", padx=5)
        tk.Button(controls, text="Snooze 30 min", command=lambda: self._snooze(30)).pack(side="left", padx=5)
        tk.Button(controls, text="Refresh", command=self._refresh).pack(side="left", padx=5)

    def _refresh(self) -> None:
        self.listbox.delete(0, tk.END)
        schedules = self.app.services["notifications"].due_schedules()
        if not schedules:
            self.listbox.insert(tk.END, "No due reminders.")
            return
        for item in schedules:
            self.listbox.insert(
                tk.END,
                f"{item['schedule_id']} - {item['pet_name']} | {item['title']} ({item['event_type']}) due {item['due_datetime']}",
            )

    def _selected_schedule_id(self) -> int | None:
        selection = self.listbox.curselection()
        if not selection:
            return None
        text = self.listbox.get(selection[0])
        if "-" not in text:
            return None
        return int(text.split("-")[0].strip())

    def _mark_done(self) -> None:
        schedule_id = self._selected_schedule_id()
        if not schedule_id:
            messagebox.showinfo("Notifications", "Select a reminder.")
            return
        self.app.services["notifications"].mark_done(schedule_id, self.app.session.user["user_id"])
        messagebox.showinfo("Done", "Reminder marked as done.")
        self._refresh()

    def _snooze(self, minutes: int) -> None:
        schedule_id = self._selected_schedule_id()
        if not schedule_id:
            messagebox.showinfo("Notifications", "Select a reminder.")
            return
        self.app.services["notifications"].snooze(schedule_id, minutes)
        messagebox.showinfo("Snoozed", f"Snoozed for {minutes} minutes.")
        self._refresh()
