from __future__ import annotations

import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, simpledialog

from PIL import Image, ImageTk

from app.views.base_view import BaseView


class PetProfileView(BaseView):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, app, "Pet Profiles")
        self.selected_pet_id: int | None = None
        self.photo_path: str | None = None
        self.photo_image = None
        self._build_content()
        self._load_pets()

    def _build_content(self) -> None:
        header = tk.Label(self.content, text="Pet Profiles", font=("Helvetica", 18, "bold"), bg="#f6f7fb")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        layout = tk.Frame(self.content, bg="#f6f7fb")
        layout.pack(fill="both", expand=True, padx=20, pady=10)
        layout.columnconfigure(0, weight=1)
        layout.columnconfigure(1, weight=2)

        self.pet_list = tk.Listbox(layout, height=20)
        self.pet_list.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        self.pet_list.bind("<<ListboxSelect>>", self._on_select)

        form = tk.Frame(layout, bg="white", padx=20, pady=20)
        form.grid(row=0, column=1, sticky="nsew")

        self.fields = {}
        labels = [
            ("Name", "name"),
            ("DOB (YYYY-MM-DD)", "dob"),
            ("Breed", "breed"),
            ("Coat Color", "coat_color"),
            ("Eye Color", "eye_color"),
            ("Owner Phone", "owner_phone"),
        ]
        for idx, (label, key) in enumerate(labels):
            tk.Label(form, text=label, bg="white").grid(row=idx, column=0, sticky="w")
            entry = tk.Entry(form, width=30)
            entry.grid(row=idx, column=1, pady=5, sticky="w")
            self.fields[key] = entry

        self.age_label = tk.Label(form, text="Age: --", bg="white")
        self.age_label.grid(row=len(labels), column=1, sticky="w", pady=(0, 10))

        tk.Button(form, text="Upload Photo", command=self._upload_photo).grid(
            row=len(labels) + 1, column=0, sticky="w", pady=5
        )
        self.photo_preview = tk.Label(form, bg="white")
        self.photo_preview.grid(row=len(labels) + 1, column=1, sticky="w")

        buttons = tk.Frame(form, bg="white")
        buttons.grid(row=len(labels) + 2, column=0, columnspan=2, pady=10, sticky="w")
        tk.Button(buttons, text="Save", command=self._save_pet).pack(side="left", padx=5)
        tk.Button(buttons, text="New", command=self._reset_form).pack(side="left", padx=5)
        tk.Button(buttons, text="Delete", command=self._delete_pet).pack(side="left", padx=5)

    def _load_pets(self) -> None:
        self.pet_list.delete(0, tk.END)
        pets = self.app.services["pets"].list_pets()
        for pet in pets:
            self.pet_list.insert(tk.END, f"{pet['pet_id']} - {pet['name']}")

    def _on_select(self, _event) -> None:
        selection = self.pet_list.curselection()
        if not selection:
            return
        index = selection[0]
        pet_id = int(self.pet_list.get(index).split(" - ")[0])
        pet = self.app.services["pets"].get_pet(pet_id)
        if not pet:
            return
        self.selected_pet_id = pet_id
        for key, entry in self.fields.items():
            entry.delete(0, tk.END)
            entry.insert(0, pet[key])
        self.photo_path = pet.get("photo_path")
        self._update_age()
        self._render_photo()

    def _update_age(self) -> None:
        dob_text = self.fields["dob"].get().strip()
        try:
            dob = datetime.fromisoformat(dob_text).date()
            today = date.today()
            years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            self.age_label.config(text=f"Age: {years} years")
        except ValueError:
            self.age_label.config(text="Age: --")

    def _validate(self) -> bool:
        for key, entry in self.fields.items():
            if not entry.get().strip():
                messagebox.showerror("Validation", "All fields are required.")
                return False
        try:
            datetime.fromisoformat(self.fields["dob"].get().strip())
        except ValueError:
            messagebox.showerror("Validation", "DOB must be YYYY-MM-DD.")
            return False
        return True

    def _collect_data(self) -> dict:
        return {
            "name": self.fields["name"].get().strip(),
            "dob": self.fields["dob"].get().strip(),
            "breed": self.fields["breed"].get().strip(),
            "coat_color": self.fields["coat_color"].get().strip(),
            "eye_color": self.fields["eye_color"].get().strip(),
            "owner_phone": self.fields["owner_phone"].get().strip(),
            "photo_path": self.photo_path,
        }

    def _save_pet(self) -> None:
        if not self._validate():
            return
        data = self._collect_data()
        user_id = self.app.session.user["user_id"]
        if self.selected_pet_id:
            self.app.services["pets"].update_pet(self.selected_pet_id, data, user_id)
            messagebox.showinfo("Saved", "Pet profile updated.")
        else:
            self.selected_pet_id = self.app.services["pets"].create_pet(data, user_id)
            messagebox.showinfo("Saved", "Pet profile created.")
        self._load_pets()

    def _reset_form(self) -> None:
        self.selected_pet_id = None
        self.photo_path = None
        for entry in self.fields.values():
            entry.delete(0, tk.END)
        self.age_label.config(text="Age: --")
        self._render_photo()

    def _delete_pet(self) -> None:
        if not self.selected_pet_id:
            messagebox.showinfo("Delete", "Select a pet first.")
            return
        confirm = messagebox.askyesno("Confirm", "Delete this pet? Re-enter credentials next.")
        if not confirm:
            return
        username = self.app.session.user["username"]
        password = simpledialog.askstring("Confirm Delete", "Enter password", show="*")
        if not password:
            return
        user = self.app.services["auth"].verify_credentials(username, password)
        if not user:
            messagebox.showerror("Error", "Invalid credentials.")
            return
        self.app.services["pets"].delete_pet(self.selected_pet_id, user["user_id"])
        self._reset_form()
        self._load_pets()
        messagebox.showinfo("Deleted", "Pet profile removed.")

    def _upload_photo(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")],
        )
        if path:
            self.photo_path = path
            self._render_photo()

    def _render_photo(self) -> None:
        self.photo_preview.config(image="", text="")
        if not self.photo_path:
            self.photo_preview.config(text="No photo")
            return
        try:
            image = Image.open(self.photo_path)
            image.thumbnail((120, 120))
            self.photo_image = ImageTk.PhotoImage(image)
            self.photo_preview.config(image=self.photo_image)
        except Exception:
            self.photo_preview.config(text="Unable to load photo")
