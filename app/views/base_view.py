from __future__ import annotations

import tkinter as tk


class BaseView(tk.Frame):
    def __init__(self, parent: tk.Widget, app, title: str) -> None:
        super().__init__(parent, bg="#f6f7fb")
        self.app = app
        self.title = title
        self.nav_buttons: dict[str, tk.Button] = {}
        self._build_layout()

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        top_bar = tk.Frame(self, bg="#1f2937", height=50)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        top_bar.grid_columnconfigure(1, weight=1)

        tk.Label(
            top_bar,
            text="PAWLOG",
            fg="white",
            bg="#1f2937",
            font=("Helvetica", 16, "bold"),
        ).grid(row=0, column=0, padx=20, pady=10)

        self.search_var = tk.StringVar()
        tk.Entry(top_bar, textvariable=self.search_var, width=40).grid(row=0, column=1, padx=10)
        user_label = f"Logged in: {self.app.session.user['username']}"
        tk.Label(
            top_bar,
            text=user_label,
            fg="white",
            bg="#1f2937",
            font=("Helvetica", 10, "bold"),
        ).grid(row=0, column=2, padx=20)

        nav = tk.Frame(self, bg="#111827", width=200)
        nav.grid(row=1, column=0, sticky="nsw")
        nav.grid_propagate(False)

        nav_items = [
            ("Home", "dashboard"),
            ("Pet Profile", "pets"),
            ("Feeding Logs", "feeding"),
            ("Health Records", "health"),
            ("Notifications", "notifications"),
            ("Settings", "settings"),
            ("Logout", "logout"),
        ]

        for idx, (label, key) in enumerate(nav_items):
            btn = tk.Button(
                nav,
                text=label,
                anchor="w",
                command=lambda k=key: self._navigate(k),
                bg="#111827",
                fg="white",
                relief="flat",
                padx=20,
                pady=10,
            )
            btn.grid(row=idx, column=0, sticky="ew")
            self.nav_buttons[key] = btn

        self.content = tk.Frame(self, bg="#f6f7fb")
        self.content.grid(row=1, column=1, sticky="nsew")

    def _navigate(self, key: str) -> None:
        if key == "logout":
            self.app.logout()
            return
        self.app.show_shell(key)
