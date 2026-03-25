"""Painting Tracker desktop app for artist workflow management."""

from __future__ import annotations

import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from database import DatabaseManager


class PaintingTrackerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Painting Tracker")
        self.geometry("1000x700")
        self.minsize(900, 620)

        self.db = DatabaseManager()
        self.current_user_id: Optional[int] = None
        self.current_username: Optional[str] = None

        style = ttk.Style(self)
        style.theme_use("clam")

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        self.frames: dict[type[BaseScreen], BaseScreen] = {}
        for frame_class in (
            LoginScreen,
            DashboardScreen,
            CurrentProjectsScreen,
            FutureIdeasScreen,
            MaterialsScreen,
            GalleryScreen,
            SettingsScreen,
        ):
            frame = frame_class(container, self)
            self.frames[frame_class] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.show_screen(LoginScreen)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_screen(self, screen_class: type["BaseScreen"], **kwargs) -> None:
        screen = self.frames[screen_class]
        screen.tkraise()
        screen.on_show(**kwargs)

    def login_user(self, user_id: int, username: str) -> None:
        self.current_user_id = user_id
        self.current_username = username
        self.show_screen(DashboardScreen)

    def logout(self) -> None:
        self.current_user_id = None
        self.current_username = None
        self.show_screen(LoginScreen)

    def on_close(self) -> None:
        self.db.close()
        self.destroy()


class BaseScreen(ttk.Frame):
    def __init__(self, parent: ttk.Frame, app: PaintingTrackerApp) -> None:
        super().__init__(parent)
        self.app = app

    def on_show(self, **kwargs) -> None:
        _ = kwargs

    @staticmethod
    def create_header(parent: ttk.Frame, title: str) -> None:
        ttk.Label(parent, text=title, font=("Segoe UI", 20, "bold")).pack(pady=(10, 20))


class LoginScreen(BaseScreen):
    def __init__(self, parent: ttk.Frame, app: PaintingTrackerApp) -> None:
        super().__init__(parent, app)

        container = ttk.Frame(self)
        container.place(relx=0.5, rely=0.5, anchor="center")

        self.create_header(container, "Painting Tracker")

        form = ttk.Frame(container, padding=20)
        form.pack()

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(form, width=30)
        self.username_entry.grid(row=0, column=1, pady=5)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(form, width=30, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        self.error_label = ttk.Label(form, text="", foreground="red")
        self.error_label.grid(row=2, column=0, columnspan=2, pady=(6, 4))

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=8)

        ttk.Button(btn_frame, text="Login", width=14, command=self.handle_login).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear", width=14, command=self.clear_inputs).pack(side="left", padx=5)

        self.password_entry.bind("<Return>", lambda _event: self.handle_login())

    def on_show(self, **kwargs) -> None:
        _ = kwargs
        self.clear_inputs()
        self.username_entry.focus_set()

    def clear_inputs(self) -> None:
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.error_label.config(text="")

    def handle_login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.error_label.config(text="Please enter both username and password.")
            return

        user = self.app.db.validate_user(username, password)
        if not user:
            self.error_label.config(text="Invalid username or password.")
            return

        self.error_label.config(text="")
        self.app.login_user(user["user_id"], user["username"])


class DashboardScreen(BaseScreen):
    def __init__(self, parent: ttk.Frame, app: PaintingTrackerApp) -> None:
        super().__init__(parent, app)

        self.create_header(self, "Painting Tracker - Dashboard")
        self.subtitle = ttk.Label(self, text="", font=("Segoe UI", 11))
        self.subtitle.pack(pady=(0, 20))

        button_frame = ttk.Frame(self)
        button_frame.pack()

        buttons = [
            ("Current Projects", CurrentProjectsScreen),
            ("Future Ideas", FutureIdeasScreen),
            ("Previous Projects / Gallery", GalleryScreen),
            ("Equipment / Materials", MaterialsScreen),
            ("Settings", SettingsScreen),
        ]

        for label, target in buttons:
            ttk.Button(
                button_frame,
                text=label,
                width=30,
                command=lambda target_screen=target: self.app.show_screen(target_screen),
            ).pack(pady=6)

        ttk.Button(button_frame, text="Logout", width=30, command=self.app.logout).pack(pady=(15, 6))

    def on_show(self, **kwargs) -> None:
        _ = kwargs
        username = self.app.current_username or "User"
        self.subtitle.config(text=f"Welcome, {username}")


class CurrentProjectsScreen(BaseCRUDScreen := BaseScreen):
    def __init__(self, parent: ttk.Frame, app: PaintingTrackerApp) -> None:
        super().__init__(parent, app)
        self.create_header(self, "Current Projects")

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=8)

        columns = ("id", "title", "status", "storage", "materials")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("status", text="Status")
        self.tree.heading("storage", text="Storage Location")
        self.tree.heading("materials", text="Materials Used")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("title", width=220)
        self.tree.column("status", width=130)
        self.tree.column("storage", width=200)
        self.tree.column("materials", width=250)

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=8)

        ttk.Button(btn_frame, text="Add", width=12, command=self.add_record).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(btn_frame, text="Edit", width=12, command=self.edit_record).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(btn_frame, text="Delete", width=12, command=self.delete_record).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(btn_frame, text="Refresh", width=12, command=self.refresh_table).grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(btn_frame, text="Home", width=12, command=lambda: self.app.show_screen(DashboardScreen)).grid(row=0, column=4, padx=4, pady=4)

    def on_show(self, **kwargs) -> None:
        _ = kwargs
        self.refresh_table()

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.app.current_user_id:
            return

        paintings = self.app.db.list_paintings(self.app.current_user_id)
        for p in paintings:
            self.tree.insert(
                "",
                "end",
                values=(
                    p["painting_id"],
                    p["title"],
                    p["status"] or "",
                    p["storage_location"] or "",
                    p["materials_used"] or "",
                ),
            )

    def _selected_painting_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def add_record(self) -> None:
        PaintingFormWindow(self.app, self.refresh_table)

    def edit_record(self) -> None:
        painting_id = self._selected_painting_id()
        if not painting_id:
            messagebox.showwarning("No Selection", "Please select a painting to edit.")
            return
        PaintingFormWindow(self.app, self.refresh_table, painting_id)

    def delete_record(self) -> None:
        painting_id = self._selected_painting_id()
        if not painting_id:
            messagebox.showwarning("No Selection", "Please select a painting to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Delete selected painting?"):
            self.app.db.delete_painting(painting_id, self.app.current_user_id)
            self.refresh_table()


class FutureIdeasScreen(BaseScreen):
    def __init__(self, parent: ttk.Frame, app: PaintingTrackerApp) -> None:
        super().__init__(parent, app)
        self.create_header(self, "Future Ideas")

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=8)

        columns = ("id", "title", "details", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("details", text="Idea")
        self.tree.heading("date", text="Date Added")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("title", width=220)
        self.tree.column("details", width=360)
        self.tree.column("date", width=150, anchor="center")

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=8)

        ttk.Button(btn_frame, text="Add", width=12, command=self.add_record).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(btn_frame, text="Edit", width=12, command=self.edit_record).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(btn_frame, text="Delete", width=12, command=self.delete_record).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(btn_frame, text="Refresh", width=12, command=self.refresh_table).grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(btn_frame, text="Home", width=12, command=lambda: self.app.show_screen(DashboardScreen)).grid(row=0, column=4, padx=4, pady=4)

    def on_show(self, **kwargs) -> None:
        _ = kwargs
        self.refresh_table()

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.app.current_user_id:
            return
        for idea in self.app.db.list_ideas(self.app.current_user_id):
            self.tree.insert("", "end", values=(idea["idea_id"], idea["idea_title"], idea["idea_details"] or "", idea["date_added"] or ""))

    def _selected_idea_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def add_record(self) -> None:
        IdeaFormWindow(self.app, self.refresh_table)

    def edit_record(self) -> None:
        idea_id = self._selected_idea_id()
        if not idea_id:
            messagebox.showwarning("No Selection", "Please select an idea to edit.")
            return
        IdeaFormWindow(self.app, self.refresh_table, idea_id)

    def delete_record(self) -> None:
        idea_id = self._selected_idea_id()
        if not idea_id:
            messagebox.showwarning("No Selection", "Please select an idea to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Delete selected idea?"):
            self.app.db.delete_idea(idea_id, self.app.current_user_id)
            self.refresh_table()


class MaterialsScreen(BaseScreen):
    def __init__(self, parent: ttk.Frame, app: PaintingTrackerApp) -> None:
        super().__init__(parent, app)
        self.create_header(self, "Equipment / Materials")

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=8)

        columns = ("id", "name", "quantity", "notes")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Material/Equipment Name")
        self.tree.heading("quantity", text="Quantity")
        self.tree.heading("notes", text="Notes")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("name", width=260)
        self.tree.column("quantity", width=150)
        self.tree.column("notes", width=320)

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=8)

        ttk.Button(btn_frame, text="Add", width=12, command=self.add_record).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(btn_frame, text="Edit", width=12, command=self.edit_record).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(btn_frame, text="Delete", width=12, command=self.delete_record).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(btn_frame, text="Refresh", width=12, command=self.refresh_table).grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(btn_frame, text="Home", width=12, command=lambda: self.app.show_screen(DashboardScreen)).grid(row=0, column=4, padx=4, pady=4)

    def on_show(self, **kwargs) -> None:
        _ = kwargs
        self.refresh_table()

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.app.current_user_id:
            return
        for material in self.app.db.list_materials(self.app.current_user_id):
            self.tree.insert(
                "",
                "end",
                values=(material["material_id"], material["material_name"], material["quantity"] or "", material["notes"] or ""),
            )

    def _selected_material_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def add_record(self) -> None:
        MaterialFormWindow(self.app, self.refresh_table)

    def edit_record(self) -> None:
        material_id = self._selected_material_id()
        if not material_id:
            messagebox.showwarning("No Selection", "Please select a material record to edit.")
            return
        MaterialFormWindow(self.app, self.refresh_table, material_id)

    def delete_record(self) -> None:
        material_id = self._selected_material_id()
        if not material_id:
            messagebox.showwarning("No Selection", "Please select a material record to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Delete selected material record?"):
            self.app.db.delete_material(material_id, self.app.current_user_id)
            self.refresh_table()


class GalleryScreen(BaseScreen):
    def __init__(self, parent: ttk.Frame, app: PaintingTrackerApp) -> None:
        super().__init__(parent, app)
        self.create_header(self, "Previous Projects / Gallery")

        self.info_label = ttk.Label(
            self,
            text="Select a painting and use View Details to see its information.",
        )
        self.info_label.pack(pady=(0, 8))

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=8)

        columns = ("id", "title", "status", "image")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("status", text="Status")
        self.tree.heading("image", text="Image Path")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("title", width=240)
        self.tree.column("status", width=160)
        self.tree.column("image", width=360)

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="View Details", width=14, command=self.view_details).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="Edit", width=14, command=self.edit_record).grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text="Delete", width=14, command=self.delete_record).grid(row=0, column=2, padx=4)
        ttk.Button(btn_frame, text="Home", width=14, command=lambda: self.app.show_screen(DashboardScreen)).grid(row=0, column=3, padx=4)

    def on_show(self, **kwargs) -> None:
        _ = kwargs
        self.refresh_table()

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.app.current_user_id:
            return

        for p in self.app.db.list_paintings(self.app.current_user_id):
            image_path = p["image_path"] or "No image path"
            self.tree.insert("", "end", values=(p["painting_id"], p["title"], p["status"] or "", image_path))

    def _selected_painting_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def view_details(self) -> None:
        painting_id = self._selected_painting_id()
        if not painting_id:
            messagebox.showwarning("No Selection", "Please select a painting to view.")
            return

        painting = self.app.db.get_painting(painting_id, self.app.current_user_id)
        if not painting:
            messagebox.showerror("Error", "Painting not found.")
            return

        image_path = painting["image_path"] or "No image path saved"
        if painting["image_path"] and not os.path.exists(painting["image_path"]):
            image_status = "Image file not found at saved path."
        elif painting["image_path"]:
            image_status = "Image path exists."
        else:
            image_status = "No image selected."

        details = (
            f"Title: {painting['title']}\n"
            f"Status: {painting['status'] or '-'}\n"
            f"Storage Location: {painting['storage_location'] or '-'}\n"
            f"Materials Used: {painting['materials_used'] or '-'}\n\n"
            f"Description:\n{painting['description'] or '-'}\n\n"
            f"Image Path: {image_path}\n"
            f"Image Info: {image_status}"
        )
        messagebox.showinfo("Painting Details", details)

    def edit_record(self) -> None:
        painting_id = self._selected_painting_id()
        if not painting_id:
            messagebox.showwarning("No Selection", "Please select a painting to edit.")
            return
        PaintingFormWindow(self.app, self.refresh_table, painting_id)

    def delete_record(self) -> None:
        painting_id = self._selected_painting_id()
        if not painting_id:
            messagebox.showwarning("No Selection", "Please select a painting to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Delete selected painting?"):
            self.app.db.delete_painting(painting_id, self.app.current_user_id)
            self.refresh_table()


class SettingsScreen(BaseScreen):
    def __init__(self, parent: ttk.Frame, app: PaintingTrackerApp) -> None:
        super().__init__(parent, app)
        self.create_header(self, "Settings")

        frame = ttk.Frame(self, padding=18)
        frame.pack()

        ttk.Label(frame, text="Old Password:").grid(row=0, column=0, sticky="w", pady=6)
        self.old_password = ttk.Entry(frame, width=30, show="*")
        self.old_password.grid(row=0, column=1, pady=6)

        ttk.Label(frame, text="New Password:").grid(row=1, column=0, sticky="w", pady=6)
        self.new_password = ttk.Entry(frame, width=30, show="*")
        self.new_password.grid(row=1, column=1, pady=6)

        ttk.Label(frame, text="Confirm Password:").grid(row=2, column=0, sticky="w", pady=6)
        self.confirm_password = ttk.Entry(frame, width=30, show="*")
        self.confirm_password.grid(row=2, column=1, pady=6)

        ttk.Button(frame, text="Change Password", command=self.change_password).grid(row=3, column=0, columnspan=2, pady=(12, 6))
        ttk.Button(frame, text="Back to Home", command=lambda: self.app.show_screen(DashboardScreen)).grid(row=4, column=0, columnspan=2, pady=4)

    def on_show(self, **kwargs) -> None:
        _ = kwargs
        self.old_password.delete(0, "end")
        self.new_password.delete(0, "end")
        self.confirm_password.delete(0, "end")

    def change_password(self) -> None:
        old = self.old_password.get()
        new = self.new_password.get()
        confirm = self.confirm_password.get()

        if not old or not new or not confirm:
            messagebox.showwarning("Missing Fields", "Please fill all password fields.")
            return
        if new != confirm:
            messagebox.showerror("Mismatch", "New password and confirm password do not match.")
            return
        if len(new) < 4:
            messagebox.showwarning("Weak Password", "Use a password with at least 4 characters.")
            return

        updated = self.app.db.update_password(self.app.current_user_id, old, new)
        if not updated:
            messagebox.showerror("Error", "Old password is incorrect.")
            return

        messagebox.showinfo("Success", "Password changed successfully.")
        self.on_show()


class PaintingFormWindow(tk.Toplevel):
    def __init__(self, app: PaintingTrackerApp, on_saved_callback, painting_id: Optional[int] = None) -> None:
        super().__init__(app)
        self.app = app
        self.on_saved_callback = on_saved_callback
        self.painting_id = painting_id

        self.title("Add Painting" if painting_id is None else "Edit Painting")
        self.geometry("550x500")
        self.resizable(False, False)
        self.grab_set()

        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Title *").grid(row=0, column=0, sticky="w", pady=6)
        self.title_entry = ttk.Entry(main, width=42)
        self.title_entry.grid(row=0, column=1, pady=6)

        ttk.Label(main, text="Description").grid(row=1, column=0, sticky="nw", pady=6)
        self.description_text = tk.Text(main, width=32, height=5)
        self.description_text.grid(row=1, column=1, pady=6)

        ttk.Label(main, text="Storage Location").grid(row=2, column=0, sticky="w", pady=6)
        self.storage_entry = ttk.Entry(main, width=42)
        self.storage_entry.grid(row=2, column=1, pady=6)

        ttk.Label(main, text="Materials Used").grid(row=3, column=0, sticky="w", pady=6)
        self.materials_entry = ttk.Entry(main, width=42)
        self.materials_entry.grid(row=3, column=1, pady=6)

        ttk.Label(main, text="Status").grid(row=4, column=0, sticky="w", pady=6)
        self.status_combo = ttk.Combobox(
            main,
            width=39,
            state="readonly",
            values=["In Progress", "Completed", "On Hold", "Planned"],
        )
        self.status_combo.grid(row=4, column=1, pady=6)
        self.status_combo.set("In Progress")

        ttk.Label(main, text="Image Path").grid(row=5, column=0, sticky="w", pady=6)
        image_row = ttk.Frame(main)
        image_row.grid(row=5, column=1, sticky="w", pady=6)

        self.image_entry = ttk.Entry(image_row, width=31)
        self.image_entry.pack(side="left")
        ttk.Button(image_row, text="Browse", command=self.browse_image).pack(side="left", padx=5)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=18)
        ttk.Button(btn_frame, text="Save", width=14, command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", width=14, command=self.destroy).pack(side="left", padx=6)

        if self.painting_id:
            self.load_data()

    def browse_image(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select Painting Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All Files", "*.*")],
        )
        if selected:
            self.image_entry.delete(0, "end")
            self.image_entry.insert(0, selected)

    def load_data(self) -> None:
        painting = self.app.db.get_painting(self.painting_id, self.app.current_user_id)
        if not painting:
            messagebox.showerror("Error", "Painting not found.")
            self.destroy()
            return

        self.title_entry.insert(0, painting["title"])
        self.description_text.insert("1.0", painting["description"] or "")
        self.storage_entry.insert(0, painting["storage_location"] or "")
        self.materials_entry.insert(0, painting["materials_used"] or "")
        self.status_combo.set(painting["status"] or "In Progress")
        self.image_entry.insert(0, painting["image_path"] or "")

    def save(self) -> None:
        title = self.title_entry.get().strip()
        description = self.description_text.get("1.0", "end").strip()
        storage_location = self.storage_entry.get().strip()
        materials_used = self.materials_entry.get().strip()
        status = self.status_combo.get().strip()
        image_path = self.image_entry.get().strip()

        if not title:
            messagebox.showerror("Validation Error", "Title is required.")
            return

        if self.painting_id:
            self.app.db.update_painting(
                self.painting_id,
                title,
                description,
                status,
                storage_location,
                materials_used,
                image_path,
                self.app.current_user_id,
            )
        else:
            self.app.db.add_painting(
                title,
                description,
                status,
                storage_location,
                materials_used,
                image_path,
                self.app.current_user_id,
            )

        self.on_saved_callback()
        self.destroy()


class IdeaFormWindow(tk.Toplevel):
    def __init__(self, app: PaintingTrackerApp, on_saved_callback, idea_id: Optional[int] = None) -> None:
        super().__init__(app)
        self.app = app
        self.on_saved_callback = on_saved_callback
        self.idea_id = idea_id

        self.title("Add Idea" if idea_id is None else "Edit Idea")
        self.geometry("520x380")
        self.resizable(False, False)
        self.grab_set()

        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Title *").grid(row=0, column=0, sticky="w", pady=6)
        self.title_entry = ttk.Entry(main, width=40)
        self.title_entry.grid(row=0, column=1, pady=6)

        ttk.Label(main, text="Idea Details").grid(row=1, column=0, sticky="nw", pady=6)
        self.details_text = tk.Text(main, width=30, height=6)
        self.details_text.grid(row=1, column=1, pady=6)

        ttk.Label(main, text="Date Added").grid(row=2, column=0, sticky="w", pady=6)
        self.date_entry = ttk.Entry(main, width=40)
        self.date_entry.grid(row=2, column=1, pady=6)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=14)
        ttk.Button(btn_frame, text="Save", width=14, command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", width=14, command=self.destroy).pack(side="left", padx=6)

        if self.idea_id:
            self.load_data()
        else:
            self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def load_data(self) -> None:
        idea = self.app.db.get_idea(self.idea_id, self.app.current_user_id)
        if not idea:
            messagebox.showerror("Error", "Idea not found.")
            self.destroy()
            return
        self.title_entry.insert(0, idea["idea_title"])
        self.details_text.insert("1.0", idea["idea_details"] or "")
        self.date_entry.insert(0, idea["date_added"] or datetime.now().strftime("%Y-%m-%d"))

    def save(self) -> None:
        title = self.title_entry.get().strip()
        details = self.details_text.get("1.0", "end").strip()
        date_added = self.date_entry.get().strip() or datetime.now().strftime("%Y-%m-%d")

        if not title:
            messagebox.showerror("Validation Error", "Title is required.")
            return

        if self.idea_id:
            self.app.db.update_idea(self.idea_id, title, details, date_added, self.app.current_user_id)
        else:
            self.app.db.add_idea(title, details, date_added, self.app.current_user_id)

        self.on_saved_callback()
        self.destroy()


class MaterialFormWindow(tk.Toplevel):
    def __init__(self, app: PaintingTrackerApp, on_saved_callback, material_id: Optional[int] = None) -> None:
        super().__init__(app)
        self.app = app
        self.on_saved_callback = on_saved_callback
        self.material_id = material_id

        self.title("Add Material" if material_id is None else "Edit Material")
        self.geometry("500x320")
        self.resizable(False, False)
        self.grab_set()

        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Material/Equipment Name *").grid(row=0, column=0, sticky="w", pady=8)
        self.name_entry = ttk.Entry(main, width=36)
        self.name_entry.grid(row=0, column=1, pady=8)

        ttk.Label(main, text="Quantity").grid(row=1, column=0, sticky="w", pady=8)
        self.quantity_entry = ttk.Entry(main, width=36)
        self.quantity_entry.grid(row=1, column=1, pady=8)

        ttk.Label(main, text="Notes").grid(row=2, column=0, sticky="w", pady=8)
        self.notes_entry = ttk.Entry(main, width=36)
        self.notes_entry.grid(row=2, column=1, pady=8)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=14)
        ttk.Button(btn_frame, text="Save", width=14, command=self.save).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", width=14, command=self.destroy).pack(side="left", padx=6)

        if self.material_id:
            self.load_data()

    def load_data(self) -> None:
        material = self.app.db.get_material(self.material_id, self.app.current_user_id)
        if not material:
            messagebox.showerror("Error", "Material record not found.")
            self.destroy()
            return

        self.name_entry.insert(0, material["material_name"])
        self.quantity_entry.insert(0, material["quantity"] or "")
        self.notes_entry.insert(0, material["notes"] or "")

    def save(self) -> None:
        name = self.name_entry.get().strip()
        quantity = self.quantity_entry.get().strip()
        notes = self.notes_entry.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Material/Equipment name is required.")
            return

        if self.material_id:
            self.app.db.update_material(self.material_id, name, quantity, notes, self.app.current_user_id)
        else:
            self.app.db.add_material(name, quantity, notes, self.app.current_user_id)

        self.on_saved_callback()
        self.destroy()


if __name__ == "__main__":
    app = PaintingTrackerApp()
    app.mainloop()
