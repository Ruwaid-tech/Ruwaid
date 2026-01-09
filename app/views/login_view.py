from __future__ import annotations

import tkinter as tk
from tkinter import messagebox


class LoginView(tk.Frame):
    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, bg="#0f172a")
        self.app = app
        self._build()

    def _build(self) -> None:
        card = tk.Frame(self, bg="white", padx=30, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="Welcome to Pawlog", font=("Helvetica", 18, "bold"), bg="white").pack(
            pady=(0, 20)
        )

        tk.Label(card, text="Username", bg="white").pack(anchor="w")
        self.username_var = tk.StringVar()
        tk.Entry(card, textvariable=self.username_var, width=30).pack(pady=(0, 10))

        tk.Label(card, text="Password", bg="white").pack(anchor="w")
        self.password_var = tk.StringVar()
        tk.Entry(card, textvariable=self.password_var, width=30, show="*").pack(pady=(0, 20))

        tk.Button(card, text="Login", command=self._login, width=20).pack()

    def _login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not username or not password:
            messagebox.showerror("Missing Info", "Enter username and password.")
            return
        user = self.app.services["auth"].verify_credentials(username, password)
        if not user:
            self.username_var.set("")
            self.password_var.set("")
            messagebox.showerror("Login Failed", "Invalid credentials. Try again.")
            return
        messagebox.showinfo("Welcome", f"Hello, {user['username']}!")
        self.app.login(user)
