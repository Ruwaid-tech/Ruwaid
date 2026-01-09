from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.views.base_view import BaseView


class HealthRecordsView(BaseView):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, app, "Health Records")
        self._build_content()
        self._load_pets()

    def _build_content(self) -> None:
        header = tk.Label(self.content, text="Health Records", font=("Helvetica", 18, "bold"), bg="#f6f7fb")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        self.pet_var = tk.StringVar()
        self.pet_menu = tk.OptionMenu(self.content, self.pet_var, "")
        self.pet_menu.pack(anchor="w", padx=20)

        record_frame = tk.Frame(self.content, bg="white", padx=20, pady=20)
        record_frame.pack(fill="x", padx=20, pady=10)

        self.record_type = tk.StringVar(value="vet")
        tk.Label(record_frame, text="Type", bg="white").grid(row=0, column=0, sticky="w")
        tk.OptionMenu(record_frame, self.record_type, "vet", "vaccination", "medication", "exercise").grid(
            row=0, column=1, sticky="w"
        )

        self.record_date = tk.StringVar(value=datetime.today().date().isoformat())
        tk.Label(record_frame, text="Date", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(record_frame, textvariable=self.record_date).grid(row=1, column=1, sticky="w")

        self.record_title = tk.StringVar()
        tk.Label(record_frame, text="Title", bg="white").grid(row=2, column=0, sticky="w")
        tk.Entry(record_frame, textvariable=self.record_title).grid(row=2, column=1, sticky="w")

        self.record_notes = tk.StringVar()
        tk.Label(record_frame, text="Notes", bg="white").grid(row=3, column=0, sticky="w")
        tk.Entry(record_frame, textvariable=self.record_notes, width=40).grid(row=3, column=1, sticky="w")

        self.record_dosage = tk.StringVar()
        tk.Label(record_frame, text="Dosage", bg="white").grid(row=4, column=0, sticky="w")
        tk.Entry(record_frame, textvariable=self.record_dosage).grid(row=4, column=1, sticky="w")

        tk.Button(record_frame, text="Add Record", command=self._add_record).grid(row=5, column=0, pady=10)

        schedule_frame = tk.Frame(self.content, bg="white", padx=20, pady=20)
        schedule_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(schedule_frame, text="Schedule Reminder", font=("Helvetica", 12, "bold"), bg="white").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )

        self.schedule_type = tk.StringVar(value="medication")
        tk.Label(schedule_frame, text="Event Type", bg="white").grid(row=1, column=0, sticky="w")
        tk.OptionMenu(schedule_frame, self.schedule_type, "medication", "vaccination", "vet").grid(
            row=1, column=1, sticky="w"
        )

        self.schedule_title = tk.StringVar()
        tk.Label(schedule_frame, text="Title", bg="white").grid(row=2, column=0, sticky="w")
        tk.Entry(schedule_frame, textvariable=self.schedule_title).grid(row=2, column=1, sticky="w")

        self.schedule_due = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        tk.Label(schedule_frame, text="Due (YYYY-MM-DD HH:MM)", bg="white").grid(row=3, column=0, sticky="w")
        tk.Entry(schedule_frame, textvariable=self.schedule_due).grid(row=3, column=1, sticky="w")

        self.schedule_repeat = tk.StringVar()
        tk.Label(schedule_frame, text="Repeat Rule", bg="white").grid(row=4, column=0, sticky="w")
        tk.Entry(schedule_frame, textvariable=self.schedule_repeat).grid(row=4, column=1, sticky="w")

        tk.Button(schedule_frame, text="Add Reminder", command=self._add_schedule).grid(row=5, column=0, pady=10)

        weight_frame = tk.Frame(self.content, bg="white", padx=20, pady=20)
        weight_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(weight_frame, text="Weight Tracker", font=("Helvetica", 12, "bold"), bg="white").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )

        self.weight_date = tk.StringVar(value=datetime.today().date().isoformat())
        tk.Label(weight_frame, text="Date", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(weight_frame, textvariable=self.weight_date).grid(row=1, column=1, sticky="w")

        self.weight_value = tk.StringVar()
        tk.Label(weight_frame, text="Weight (kg)", bg="white").grid(row=2, column=0, sticky="w")
        tk.Entry(weight_frame, textvariable=self.weight_value).grid(row=2, column=1, sticky="w")

        tk.Button(weight_frame, text="Add Weight", command=self._add_weight).grid(row=3, column=0, pady=10)

        self.chart_frame = tk.Frame(self.content, bg="#f6f7fb")
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.records_list = tk.Listbox(self.content, height=8)
        self.records_list.pack(fill="x", padx=20, pady=10)

    def _load_pets(self) -> None:
        pets = self.app.services["pets"].list_pets()
        menu = self.pet_menu["menu"]
        menu.delete(0, "end")
        if not pets:
            self.pet_var.set("")
            menu.add_command(label="No pets", command=lambda: None)
        else:
            for pet in pets:
                menu.add_command(label=f"{pet['pet_id']} - {pet['name']}", command=lambda p=pet: self._select_pet(p))
            self._select_pet(pets[0])

    def _select_pet(self, pet: dict) -> None:
        self.pet_var.set(f"{pet['pet_id']} - {pet['name']}")
        self._refresh_records()
        self._render_weight_chart()

    def _selected_pet_id(self) -> int | None:
        if not self.pet_var.get():
            return None
        return int(self.pet_var.get().split(" - ")[0])

    def _add_record(self) -> None:
        pet_id = self._selected_pet_id()
        if not pet_id:
            messagebox.showerror("Validation", "Select a pet.")
            return
        if not self.record_title.get().strip():
            messagebox.showerror("Validation", "Title required.")
            return
        try:
            datetime.fromisoformat(self.record_date.get().strip())
        except ValueError:
            messagebox.showerror("Validation", "Invalid date.")
            return
        self.app.services["health"].add_record(
            {
                "pet_id": pet_id,
                "type": self.record_type.get(),
                "date": self.record_date.get().strip(),
                "title": self.record_title.get().strip(),
                "notes": self.record_notes.get().strip(),
                "dosage": self.record_dosage.get().strip(),
            },
            self.app.session.user["user_id"],
        )
        messagebox.showinfo("Saved", "Health record added.")
        self._refresh_records()

    def _add_schedule(self) -> None:
        pet_id = self._selected_pet_id()
        if not pet_id:
            messagebox.showerror("Validation", "Select a pet.")
            return
        if not self.schedule_title.get().strip():
            messagebox.showerror("Validation", "Title required.")
            return
        try:
            datetime.fromisoformat(self.schedule_due.get().strip())
        except ValueError:
            messagebox.showerror("Validation", "Invalid due datetime.")
            return
        self.app.services["health"].add_schedule(
            {
                "pet_id": pet_id,
                "event_type": self.schedule_type.get(),
                "title": self.schedule_title.get().strip(),
                "due_datetime": self.schedule_due.get().strip(),
                "repeat_rule": self.schedule_repeat.get().strip(),
            },
            self.app.session.user["user_id"],
        )
        messagebox.showinfo("Saved", "Reminder scheduled.")

    def _add_weight(self) -> None:
        pet_id = self._selected_pet_id()
        if not pet_id:
            messagebox.showerror("Validation", "Select a pet.")
            return
        try:
            datetime.fromisoformat(self.weight_date.get().strip())
            weight = float(self.weight_value.get().strip())
        except ValueError:
            messagebox.showerror("Validation", "Enter a valid date and weight.")
            return
        self.app.services["health"].add_weight(pet_id, self.weight_date.get().strip(), weight, self.app.session.user["user_id"])
        messagebox.showinfo("Saved", "Weight log added.")
        self._render_weight_chart()

    def _refresh_records(self) -> None:
        self.records_list.delete(0, tk.END)
        pet_id = self._selected_pet_id()
        if not pet_id:
            return
        records = self.app.services["health"].list_records(pet_id)
        for rec in records:
            self.records_list.insert(
                tk.END,
                f"{rec['date']} - {rec['type']} - {rec['title']} ({rec.get('created_by_name','')})",
            )
        if not records:
            self.records_list.insert(tk.END, "No health records.")

    def _render_weight_chart(self) -> None:
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        pet_id = self._selected_pet_id()
        if not pet_id:
            return
        weights = self.app.services["health"].list_weights(pet_id)
        if not weights:
            tk.Label(self.chart_frame, text="No weight logs yet.", bg="#f6f7fb").pack()
            return
        dates = [datetime.fromisoformat(row["date"]).date() for row in weights]
        values = [row["weight_kg"] for row in weights]
        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(dates, values, marker="o")
        ax.set_title("Weight Trend")
        ax.set_ylabel("kg")
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
