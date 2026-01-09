from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.views.base_view import BaseView


class DashboardView(BaseView):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, app, "Dashboard")
        self._build_content()
        self._refresh()

    def _build_content(self) -> None:
        header = tk.Label(self.content, text="Dashboard", font=("Helvetica", 18, "bold"), bg="#f6f7fb")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        actions = tk.Frame(self.content, bg="#f6f7fb")
        actions.pack(fill="x", padx=20)

        tk.Button(actions, text="Add Pet", command=lambda: self.app.show_shell("pets")).pack(
            side="left", padx=5
        )
        tk.Button(actions, text="Log Feeding", command=lambda: self.app.show_shell("feeding")).pack(
            side="left", padx=5
        )
        tk.Button(actions, text="Add Vaccination", command=lambda: self.app.show_shell("health")).pack(
            side="left", padx=5
        )
        tk.Button(actions, text="View Health Score", command=self._show_health_score).pack(
            side="left", padx=5
        )

        main = tk.Frame(self.content, bg="#f6f7fb")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=1)

        self.overview = tk.Frame(main, bg="white", padx=15, pady=15)
        self.overview.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.reminders = tk.Frame(main, bg="white", padx=15, pady=15)
        self.reminders.grid(row=0, column=1, sticky="nsew")

        tk.Label(self.overview, text="Health Overview", font=("Helvetica", 14, "bold"), bg="white").pack(
            anchor="w"
        )
        self.health_score_label = tk.Label(self.overview, text="Latest Score: --", bg="white")
        self.health_score_label.pack(anchor="w", pady=(10, 5))

        self.chart_frame = tk.Frame(self.overview, bg="white")
        self.chart_frame.pack(fill="both", expand=True)

        tk.Label(self.reminders, text="Today's Reminders", font=("Helvetica", 14, "bold"), bg="white").pack(
            anchor="w"
        )
        self.reminder_list = tk.Listbox(self.reminders, height=8)
        self.reminder_list.pack(fill="both", expand=True, pady=10)

        tk.Label(self.reminders, text="Recent Activity", font=("Helvetica", 14, "bold"), bg="white").pack(
            anchor="w", pady=(10, 0)
        )
        self.activity_list = tk.Listbox(self.reminders, height=8)
        self.activity_list.pack(fill="both", expand=True, pady=10)

    def _refresh(self) -> None:
        pets = self.app.services["pets"].list_pets()
        if pets:
            score = self.app.services["score"].compute_score(pets[0]["pet_id"])
            self.health_score_label.config(text=f"Latest Score: {score['total']}")
            self._render_weight_chart(pets[0]["pet_id"])
        else:
            self.health_score_label.config(text="Latest Score: --")
            for widget in self.chart_frame.winfo_children():
                widget.destroy()
            tk.Label(self.chart_frame, text="No pets yet.", bg="white").pack()

        self.reminder_list.delete(0, tk.END)
        reminders = self.app.services["notifications"].due_schedules()
        for item in reminders:
            due = item["due_datetime"]
            self.reminder_list.insert(
                tk.END, f"{item['pet_name']} - {item['title']} ({item['event_type']}) @ {due}"
            )
        if not reminders:
            self.reminder_list.insert(tk.END, "No due reminders.")

        self.activity_list.delete(0, tk.END)
        activities = self.app.services["audit"].recent()
        for act in activities:
            timestamp = act["timestamp"]
            user = act.get("username") or "Unknown"
            self.activity_list.insert(
                tk.END, f"{timestamp} - {user} {act['action']} {act['entity_type']} #{act['entity_id']}"
            )
        if not activities:
            self.activity_list.insert(tk.END, "No recent activity.")

    def _render_weight_chart(self, pet_id: int) -> None:
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        weights = self.app.services["health"].list_weights(pet_id)
        if not weights:
            tk.Label(self.chart_frame, text="No weight logs yet.", bg="white").pack()
            return
        dates = [datetime.fromisoformat(row["date"]).date() for row in weights]
        values = [row["weight_kg"] for row in weights]
        fig = Figure(figsize=(4, 2.5), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(dates, values, marker="o")
        ax.set_title("Weight Trend")
        ax.set_ylabel("kg")
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _show_health_score(self) -> None:
        pets = self.app.services["pets"].list_pets()
        if not pets:
            messagebox.showinfo("Health Score", "Add a pet first.")
            return
        pet = pets[0]
        score = self.app.services["score"].compute_score(pet["pet_id"])
        window = tk.Toplevel(self)
        window.title("Health Score")
        tk.Label(window, text=f"{pet['name']} Health Score", font=("Helvetica", 14, "bold")).pack(pady=10)
        tk.Label(window, text=f"Total Score: {score['total']}").pack()
        tk.Label(window, text=score["explanation"], wraplength=400, justify="left").pack(pady=10)

        fig = Figure(figsize=(4, 3), dpi=100)
        ax = fig.add_subplot(111)
        labels = list(score["components"].keys())
        values = list(score["components"].values())
        ax.pie(values, labels=labels, autopct="%1.0f%%")
        ax.set_title("Score Breakdown")
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
