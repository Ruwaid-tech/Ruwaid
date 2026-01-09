from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from app.views.base_view import BaseView


class SettingsView(BaseView):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, app, "Settings")
        self._build_content()

    def _build_content(self) -> None:
        header = tk.Label(self.content, text="Settings", font=("Helvetica", 18, "bold"), bg="#f6f7fb")
        header.pack(anchor="w", padx=20, pady=(20, 10))

        account = tk.Frame(self.content, bg="white", padx=20, pady=20)
        account.pack(fill="x", padx=20, pady=10)

        tk.Label(account, text="Account", font=("Helvetica", 12, "bold"), bg="white").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.username_var = tk.StringVar(value=self.app.session.user["username"])
        tk.Label(account, text="Username", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(account, textvariable=self.username_var).grid(row=1, column=1, sticky="w")
        tk.Button(account, text="Update Username", command=self._update_username).grid(
            row=1, column=2, padx=5
        )

        self.password_var = tk.StringVar()
        tk.Label(account, text="New Password", bg="white").grid(row=2, column=0, sticky="w")
        tk.Entry(account, textvariable=self.password_var, show="*").grid(row=2, column=1, sticky="w")
        tk.Button(account, text="Update Password", command=self._update_password).grid(
            row=2, column=2, padx=5
        )

        prefs = tk.Frame(self.content, bg="white", padx=20, pady=20)
        prefs.pack(fill="x", padx=20, pady=10)
        tk.Label(prefs, text="Preferences", font=("Helvetica", 12, "bold"), bg="white").pack(anchor="w")
        tk.Checkbutton(prefs, text="Enable notifications", bg="white").pack(anchor="w")
        tk.Checkbutton(prefs, text="Auto logout enabled", bg="white").pack(anchor="w")
        tk.Label(prefs, text="Theme (placeholder)", bg="white").pack(anchor="w")
        tk.Label(prefs, text="Language (placeholder)", bg="white").pack(anchor="w")

        if self.app.session.user["role"] == "Admin":
            admin_frame = tk.Frame(self.content, bg="white", padx=20, pady=20)
            admin_frame.pack(fill="x", padx=20, pady=10)
            tk.Label(admin_frame, text="User Management", font=("Helvetica", 12, "bold"), bg="white").grid(
                row=0, column=0, columnspan=2, sticky="w"
            )
            self.new_user = tk.StringVar()
            self.new_password = tk.StringVar()
            self.new_role = tk.StringVar(value="Employee")
            tk.Label(admin_frame, text="Username", bg="white").grid(row=1, column=0, sticky="w")
            tk.Entry(admin_frame, textvariable=self.new_user).grid(row=1, column=1, sticky="w")
            tk.Label(admin_frame, text="Password", bg="white").grid(row=2, column=0, sticky="w")
            tk.Entry(admin_frame, textvariable=self.new_password, show="*").grid(row=2, column=1, sticky="w")
            tk.Label(admin_frame, text="Role", bg="white").grid(row=3, column=0, sticky="w")
            tk.OptionMenu(admin_frame, self.new_role, "Admin", "Employee").grid(row=3, column=1, sticky="w")
            tk.Button(admin_frame, text="Create User", command=self._create_user).grid(
                row=4, column=0, pady=10
            )

    def _update_username(self) -> None:
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Validation", "Username cannot be empty.")
            return
        self.app.services["user"].update_username(self.app.session.user["user_id"], username)
        self.app.session.user["username"] = username
        messagebox.showinfo("Saved", "Username updated. Please re-login for full refresh.")

    def _update_password(self) -> None:
        password = self.password_var.get().strip()
        if len(password) < 6:
            messagebox.showerror("Validation", "Password must be at least 6 characters.")
            return
        self.app.services["auth"].update_password(self.app.session.user["user_id"], password)
        self.password_var.set("")
        messagebox.showinfo("Saved", "Password updated.")

    def _create_user(self) -> None:
        username = self.new_user.get().strip()
        password = self.new_password.get().strip()
        role = self.new_role.get()
        if not username or not password:
            messagebox.showerror("Validation", "Username and password required.")
            return
        self.app.services["auth"].create_user(username, password, role)
        messagebox.showinfo("Saved", "User created.")
        self.new_user.set("")
        self.new_password.set("")
