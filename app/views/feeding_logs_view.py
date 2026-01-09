from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from app.views.base_view import BaseView


class FeedingLogsView(BaseView):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, app, "Feeding Logs")
        self._build_content()
        self._load_pets()

    def _build_content(self) -> None:
        header = tk.Label(self.content, text="Feeding Logs", font=("Helvetica", 18, "bold"), bg="#f6f7fb")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        form = tk.Frame(self.content, bg="white", padx=20, pady=20)
        form.pack(fill="x", padx=20)

        self.pet_var = tk.StringVar()
        self.pet_menu = tk.OptionMenu(form, self.pet_var, "")
        tk.Label(form, text="Pet", bg="white").grid(row=0, column=0, sticky="w")
        self.pet_menu.grid(row=0, column=1, sticky="w")

        self.date_var = tk.StringVar(value=datetime.today().date().isoformat())
        tk.Label(form, text="Date (YYYY-MM-DD)", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(form, textvariable=self.date_var).grid(row=1, column=1, sticky="w")

        self.time_var = tk.StringVar(value="09:00")
        tk.Label(form, text="Time (HH:MM)", bg="white").grid(row=2, column=0, sticky="w")
        tk.Entry(form, textvariable=self.time_var).grid(row=2, column=1, sticky="w")

        self.food_var = tk.StringVar()
        tk.Label(form, text="Food Type", bg="white").grid(row=3, column=0, sticky="w")
        tk.Entry(form, textvariable=self.food_var).grid(row=3, column=1, sticky="w")

        self.amount_var = tk.StringVar()
        tk.Label(form, text="Amount", bg="white").grid(row=4, column=0, sticky="w")
        tk.Entry(form, textvariable=self.amount_var).grid(row=4, column=1, sticky="w")

        self.unit_var = tk.StringVar(value="g")
        tk.Label(form, text="Unit", bg="white").grid(row=5, column=0, sticky="w")
        tk.Entry(form, textvariable=self.unit_var, width=5).grid(row=5, column=1, sticky="w")

        tk.Button(form, text="Add Feeding", command=self._add_feeding).grid(row=6, column=0, pady=10)

        list_area = tk.Frame(self.content, bg="#f6f7fb")
        list_area.pack(fill="both", expand=True, padx=20, pady=10)
        list_area.columnconfigure(0, weight=1)
        list_area.columnconfigure(1, weight=1)

        self.today_list = tk.Listbox(list_area)
        self.today_list.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right_panel = tk.Frame(list_area, bg="#f6f7fb")
        right_panel.grid(row=0, column=1, sticky="nsew")

        tk.Label(right_panel, text="History", bg="#f6f7fb", font=("Helvetica", 12, "bold")).pack(anchor="w")
        self.history_list = tk.Listbox(right_panel)
        self.history_list.pack(fill="both", expand=True)
        tk.Button(right_panel, text="Mark Completed", command=self._mark_completed).pack(pady=10)

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
        self._refresh_lists()

    def _selected_pet_id(self) -> int | None:
        if not self.pet_var.get():
            return None
        return int(self.pet_var.get().split(" - ")[0])

    def _add_feeding(self) -> None:
        pet_id = self._selected_pet_id()
        if not pet_id:
            messagebox.showerror("Validation", "Select a pet.")
            return
        try:
            scheduled = f"{self.date_var.get().strip()} {self.time_var.get().strip()}"
            datetime.fromisoformat(scheduled)
            amount = float(self.amount_var.get().strip())
        except ValueError:
            messagebox.showerror("Validation", "Enter valid date, time, and amount.")
            return
        if not self.food_var.get().strip():
            messagebox.showerror("Validation", "Food type required.")
            return
        self.app.services["feeding"].add_feeding(
            {
                "pet_id": pet_id,
                "scheduled_datetime": scheduled,
                "food_type": self.food_var.get().strip(),
                "amount": amount,
                "unit": self.unit_var.get().strip() or "g",
            },
            self.app.session.user["user_id"],
        )
        self._refresh_lists()
        messagebox.showinfo("Saved", "Feeding entry added.")

    def _refresh_lists(self) -> None:
        pet_id = self._selected_pet_id()
        if not pet_id:
            return
        self.today_list.delete(0, tk.END)
        date_str = self.date_var.get().strip()
        today_items = self.app.services["feeding"].list_feedings_for_day(pet_id, date_str)
        for row in today_items:
            status = "✅" if row["completed_at"] else "⬜"
            self.today_list.insert(
                tk.END,
                f"{status} {row['scheduled_datetime']} - {row['food_type']} {row['amount']}{row['unit']} (ID {row['feed_id']})",
            )
        if not today_items:
            self.today_list.insert(tk.END, "No feedings for this day.")

        self.history_list.delete(0, tk.END)
        history = self.app.services["feeding"].list_recent_feedings(pet_id)
        for row in history:
            completed = row["completed_at"] or "pending"
            self.history_list.insert(
                tk.END,
                f"{row['scheduled_datetime']} - {row['food_type']} ({completed}) - ID {row['feed_id']}",
            )
        if not history:
            self.history_list.insert(tk.END, "No feeding history.")

    def _mark_completed(self) -> None:
        selection = self.history_list.curselection()
        if not selection:
            messagebox.showinfo("Complete", "Select a feeding log in History.")
            return
        text = self.history_list.get(selection[0])
        if "ID" not in text:
            return
        feed_id = int(text.split("ID")[-1].strip())
        self.app.services["feeding"].complete_feeding(feed_id, self.app.session.user["user_id"])
        self._refresh_lists()
        messagebox.showinfo("Completed", "Feeding marked as completed.")
