"""Kitchen Manager desktop application built with Tkinter and SQLite."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont, messagebox, ttk
from typing import Callable, Dict, List, Optional

from database import DatabaseManager, RecipeStep, Supplier, VendorOrder, CustomerOrder

UNIT_DEFINITIONS: Dict[str, tuple[str, float]] = {
    "kg": ("g", 1000.0),
    "g": ("g", 1.0),
    "L": ("ml", 1000.0),
    "ml": ("ml", 1.0),
    "unit": ("unit", 1.0),
    "dozen": ("unit", 12.0),
}

THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "Light": {
        "background": "#f7f9fc",
        "surface": "#ffffff",
        "text": "#1f2933",
        "muted": "#4b5563",
        "border": "#d6d9df",
        "accent": "#2563eb",
        "on_accent": "#f8fafc",
        "warning": "#d97706",
    },
    "Dark": {
        "background": "#111827",
        "surface": "#1f2933",
        "text": "#f8fafc",
        "muted": "#cbd5f5",
        "border": "#374151",
        "accent": "#38bdf8",
        "on_accent": "#0f172a",
        "warning": "#fbbf24",
    },
}


FONT_CACHE: Dict[tuple[int, str, str], tkfont.Font] = {}


def get_font(size: int, weight: str = "normal", slant: str = "roman") -> tkfont.Font:
    """Return a cached Tk font for consistent cross-platform rendering."""

    key = (size, weight, slant)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = tkfont.Font(family="Segoe UI", size=size, weight=weight, slant=slant)
    return FONT_CACHE[key]


def format_quantity(amount_base: float, conversion: float) -> str:
    return f"{amount_base / conversion:.2f}"


def compute_recipe_usage(db: DatabaseManager, recipe_id: int, multiplier: float = 1.0) -> tuple[List[tuple[int, float]], List[str]]:
    """Return usage pairs in base units and human friendly missing messages."""

    usage: List[tuple[int, float]] = []
    missing: List[str] = []
    for ingredient in db.get_recipe_ingredients(recipe_id):
        item = db.get_inventory_item(ingredient.inventory_item_id)
        if item is None:
            missing.append("Unknown inventory item linked to recipe")
            continue
        required = ingredient.quantity_base * multiplier
        if item.quantity_base < required:
            amount = format_quantity(required, item.conversion_to_base)
            missing.append(f"{item.name} requires {amount} {item.display_unit}")
        else:
            usage.append((item.id, required))
    return usage, missing


class KitchenManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Kitchen Manager")
        self.geometry("1100x760")
        self.minsize(960, 700)
        try:
            default_font = tkfont.nametofont("TkDefaultFont")
            default_font.configure(family="Segoe UI", size=11)
        except tk.TclError:
            pass
        self.style = ttk.Style(self)
        self.available_themes = tuple(THEME_PALETTES.keys())
        self.theme_observers: List[Callable[[Dict[str, str]], None]] = []
        self.current_palette: Dict[str, str] = {}

        self.db = DatabaseManager()
        self.current_user: Optional[str] = None

        initial_theme = self.db.get_setting("theme", "Light")
        self.apply_theme(initial_theme)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.frames: Dict[type[BaseFrame], BaseFrame] = {}
        for frame_cls in (
            LoginFrame,
            RegisterFrame,
            DashboardFrame,
            InventoryFrame,
            InventoryEditFrame,
            SuppliersFrame,
            VendorOrdersFrame,
            CustomerOrdersFrame,
            RecipeFrame,
            ReportsFrame,
            SettingsFrame,
        ):
            frame = frame_cls(container, self)
            self.frames[frame_cls] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginFrame)

    # Navigation helpers -------------------------------------------------
    def show_frame(self, frame_cls: type["BaseFrame"], **kwargs) -> None:
        frame = self.frames[frame_cls]
        frame.tkraise()
        frame.on_show(**kwargs)

    def add_theme_observer(self, callback: Callable[[Dict[str, str]], None]) -> None:
        self.theme_observers.append(callback)
        if self.current_palette:
            callback(self.current_palette)

    def apply_theme(self, desired: str) -> None:
        theme = "Dark" if desired.lower().startswith("dark") else "Light"
        palette = THEME_PALETTES[theme]
        self.current_palette = palette
        self.style.theme_use("clam")

        self.configure(bg=palette["background"])

        self.style.configure("TFrame", background=palette["background"])
        self.style.configure("TLabel", background=palette["background"], foreground=palette["text"])
        self.style.configure("TButton", background=palette["surface"], foreground=palette["text"])
        self.style.configure("TEntry", fieldbackground=palette["surface"], foreground=palette["text"])
        self.style.configure("TCombobox", fieldbackground=palette["surface"], foreground=palette["text"])
        self.style.configure("Treeview", background=palette["surface"], fieldbackground=palette["surface"], foreground=palette["text"])
        self.style.configure("Treeview.Heading", background=palette["surface"], foreground=palette["muted"])
        self.style.configure("TLabelframe", background=palette["surface"], bordercolor=palette["border"], relief=tk.SOLID)
        self.style.configure("TLabelframe.Label", background=palette["surface"], foreground=palette["muted"])
        self.style.configure("TNotebook", background=palette["background"], foreground=palette["text"])
        self.style.map(
            "TButton",
            background=[("pressed", palette["accent"]), ("active", palette["accent"])],
            foreground=[("pressed", palette["on_accent"]), ("active", palette["on_accent"])],
        )
        self.style.map(
            "Treeview",
            background=[("selected", palette["accent"])],
            foreground=[("selected", palette["on_accent"])],
        )

        for callback in self.theme_observers:
            callback(palette)

    def on_login(self, username: str) -> None:
        self.current_user = username
        messagebox.showinfo("Login successful", f"Welcome back {username}")
        dashboard: DashboardFrame = self.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.set_username(username)
        self.show_frame(DashboardFrame)

    def logout(self) -> None:
        self.current_user = None
        self.show_frame(LoginFrame)

    def destroy(self) -> None:  # type: ignore[override]
        self.db.close()
        super().destroy()


class BaseFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, padding=30)
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def on_show(self, **_: object) -> None:
        pass

    def add_nav_buttons(self, frame: ttk.Frame) -> None:
        ttk.Button(frame, text="Back to dashboard", command=lambda: self.app.show_frame(DashboardFrame)).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(frame, text="Logout", command=self.app.logout).pack(side=tk.LEFT, padx=5)

    def register_theme_observer(self, callback: Callable[[Dict[str, str]], None]) -> None:
        self.app.add_theme_observer(callback)


class LoginFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)

        ttk.Label(wrapper, text="Kitchen Manager Login", font=get_font(26, "bold")).grid(
            row=0, column=0, pady=(0, 30)
        )

        form = ttk.Frame(wrapper)
        form.grid(row=1, column=0, sticky="nsew", pady=10)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.username_entry = ttk.Entry(form)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.password_entry = ttk.Entry(form, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        buttons = ttk.Frame(wrapper)
        buttons.grid(row=2, column=0, pady=(20, 0))
        ttk.Button(buttons, text="Login", command=self.handle_login).grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Register", command=lambda: self.app.show_frame(RegisterFrame)).grid(
            row=0, column=1, padx=5
        )

    def on_show(self, **_: object) -> None:
        self.username_entry.focus_set()

    def handle_login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Missing information", "Please enter a username and password")
            return
        if self.app.db.authenticate_user(username, password):
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.app.on_login(username)
        else:
            messagebox.showerror("Login failed", "Incorrect username or password")


class RegisterFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)

        ttk.Label(wrapper, text="Create an account", font=get_font(26, "bold")).grid(
            row=0, column=0, pady=(0, 30)
        )

        form = ttk.Frame(wrapper)
        form.grid(row=1, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.username_entry = ttk.Entry(form)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.password_entry = ttk.Entry(form, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(form, text="Confirm password:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.confirm_entry = ttk.Entry(form, show="*")
        self.confirm_entry.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        buttons = ttk.Frame(wrapper)
        buttons.grid(row=2, column=0, pady=(20, 0))
        ttk.Button(buttons, text="Register", command=self.handle_register).grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Back to login", command=lambda: self.app.show_frame(LoginFrame)).grid(
            row=0, column=1, padx=5
        )

    def handle_register(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        if not username or not password:
            messagebox.showerror("Missing information", "Username and password are required")
            return
        if password != confirm:
            messagebox.showerror("Mismatch", "Passwords do not match")
            return
        if self.app.db.create_user(username, password):
            messagebox.showinfo("Success", "Account created. Please log in.")
            self.app.show_frame(LoginFrame)
        else:
            messagebox.showerror("Unavailable", "That username already exists")


class DashboardFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(2, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        self.title_var = tk.StringVar(value="KitchenMate • Dashboard")
        ttk.Label(header, textvariable=self.title_var, font=get_font(24, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.user_var = tk.StringVar(value="User:(guest)")
        ttk.Label(header, textvariable=self.user_var, font=get_font(14)).grid(row=0, column=1, sticky="e")

        ttk.Separator(wrapper, orient=tk.HORIZONTAL).grid(row=1, column=0, sticky="ew", pady=20)

        button_grid = ttk.Frame(wrapper)
        button_grid.grid(row=2, column=0, sticky="nsew")
        for col in range(4):
            button_grid.columnconfigure(col, weight=1)

        buttons = [
            ("Inventory", InventoryFrame),
            ("Edit inventory", InventoryEditFrame),
            ("Suppliers", SuppliersFrame),
            ("Vendor Orders", VendorOrdersFrame),
            ("Recipes", RecipeFrame),
            ("Customer order", CustomerOrdersFrame),
            ("Reports", ReportsFrame),
            ("Settings", SettingsFrame),
        ]
        for idx, (label, frame_cls) in enumerate(buttons):
            row, col = divmod(idx, 4)
            btn = ttk.Button(
                button_grid,
                text=label,
                command=lambda cls=frame_cls: self.app.show_frame(cls),
                width=18,
            )
            btn.grid(row=row, column=col, padx=12, pady=12, sticky="ew")

        footer = ttk.Frame(wrapper)
        footer.grid(row=3, column=0, sticky="ew", pady=(30, 0))
        ttk.Button(footer, text="Logout", command=self.app.logout).pack(side=tk.RIGHT)
        self.status_var = tk.StringVar()
        ttk.Label(footer, textvariable=self.status_var, font=get_font(12)).pack(side=tk.LEFT)

    def set_username(self, username: str) -> None:
        self.user_var.set(f"User:({username})")
        self.refresh_status()

    def refresh_status(self) -> None:
        restaurant_name = self.app.db.get_setting("restaurant_name", "KitchenMate")
        self.title_var.set(f"{restaurant_name} • Dashboard")
        pending = self.app.db.count_pending_orders()
        low_stock = self.app.db.count_low_stock_items()
        self.status_var.set(f"Status: Pending orders: {pending} • Low-stock items: {low_stock}")

    def on_show(self, **_: object) -> None:
        self.refresh_status()


class InventoryFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Inventory", font=get_font(22, "bold")).pack(side=tk.LEFT)
        nav_bar = ttk.Frame(header)
        nav_bar.pack(side=tk.RIGHT)
        self.add_nav_buttons(nav_bar)

        self.tree = ttk.Treeview(
            wrapper,
            columns=("quantity", "unit", "threshold", "status"),
            show="headings",
            selectmode="browse",
        )
        self.tree.grid(row=1, column=0, sticky="nsew", pady=20)
        for col, heading in (
            ("quantity", "Quantity"),
            ("unit", "Unit"),
            ("threshold", "Low stock at"),
            ("status", "Status"),
        ):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=140, anchor=tk.CENTER)
        self.tree.heading("#0", text="Name")
        self.tree.column("#0", width=200, anchor=tk.W)
        self.tree.bind("<<TreeviewSelect>>", lambda _: self.on_selection())

        side_panel = ttk.Frame(wrapper)
        side_panel.grid(row=1, column=1, sticky="nsw", padx=(20, 0))
        side_panel.columnconfigure(0, weight=1)

        form = ttk.LabelFrame(side_panel, text="Add / update item", padding=15)
        form.grid(row=0, column=0, sticky="new")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Name:").grid(row=0, column=0, sticky="e", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Quantity:").grid(row=1, column=0, sticky="e", pady=4)
        self.quantity_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.quantity_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Unit:").grid(row=2, column=0, sticky="e", pady=4)
        self.unit_var = tk.StringVar(value="kg")
        ttk.Combobox(form, textvariable=self.unit_var, values=list(UNIT_DEFINITIONS.keys()), state="readonly").grid(
            row=2, column=1, sticky="ew", pady=4
        )

        ttk.Label(form, text="Low stock threshold:").grid(row=3, column=0, sticky="e", pady=4)
        self.threshold_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.threshold_var).grid(row=3, column=1, sticky="ew", pady=4)

        form_buttons = ttk.Frame(form)
        form_buttons.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(form_buttons, text="Save", command=self.save_item).grid(row=0, column=0, padx=5)
        ttk.Button(form_buttons, text="Reset", command=self.reset_form).grid(row=0, column=1, padx=5)

        action_bar = ttk.Frame(side_panel)
        action_bar.grid(row=1, column=0, sticky="ew", pady=(20, 0))
        ttk.Button(action_bar, text="Delete selected", command=self.delete_selected).pack(fill=tk.X)
        ttk.Button(action_bar, text="Refresh", command=self.refresh_inventory).pack(fill=tk.X, pady=(10, 0))

        self.low_stock_var = tk.StringVar()
        self.low_stock_label = ttk.Label(side_panel, textvariable=self.low_stock_var, wraplength=280, justify=tk.LEFT)
        self.low_stock_label.grid(row=2, column=0, sticky="nw", pady=(20, 0))

        self.editing_item_id: Optional[int] = None

        self.register_theme_observer(self.apply_theme)

    def on_show(self, **_: object) -> None:
        self.refresh_inventory()

    # Inventory helpers --------------------------------------------------
    def refresh_inventory(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        items = self.app.db.get_inventory_items()
        low_stock_messages: List[str] = []
        for item in items:
            status = "LOW" if item.is_low else "OK"
            if item.is_low:
                low_stock_messages.append(f"⚠ Low stock: {item.name}")
            self.tree.insert(
                "",
                tk.END,
                iid=str(item.id),
                text=item.name,
                values=(
                    item.quantity_display,
                    item.display_unit,
                    item.threshold_display,
                    status,
                ),
            )
        if low_stock_messages:
            self.low_stock_var.set("\n".join(low_stock_messages))
        else:
            self.low_stock_var.set("All items are above their low stock thresholds.")
        self.reset_form(clear_selection=False)

    def reset_form(self, clear_selection: bool = True) -> None:
        self.editing_item_id = None
        self.name_var.set("")
        self.quantity_var.set("")
        self.threshold_var.set("")
        self.unit_var.set("kg")
        if clear_selection:
            self.tree.selection_remove(self.tree.selection())

    def on_selection(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item_id = int(selection[0])
        inventory_item = self.app.db.get_inventory_item(item_id)
        if inventory_item is None:
            return
        self.editing_item_id = item_id
        self.name_var.set(inventory_item.name)
        self.unit_var.set(inventory_item.display_unit)
        self.quantity_var.set(str(inventory_item.quantity_display))
        self.threshold_var.set(str(inventory_item.threshold_display))

    def save_item(self) -> None:
        name = self.name_var.get().strip()
        unit = self.unit_var.get()
        try:
            quantity = float(self.quantity_var.get())
            threshold = float(self.threshold_var.get())
        except ValueError:
            messagebox.showerror("Invalid number", "Quantity and threshold must be numeric values")
            return
        if not name:
            messagebox.showerror("Missing name", "Please provide an item name")
            return
        base_unit, conversion = UNIT_DEFINITIONS[unit]
        quantity_base = quantity * conversion
        threshold_base = threshold * conversion
        if self.editing_item_id is None:
            try:
                self.app.db.add_inventory_item(name, quantity_base, unit, base_unit, conversion, threshold_base)
            except Exception as exc:  # pragma: no cover - Tkinter UI guard
                messagebox.showerror("Error", f"Could not add item: {exc}")
                return
        else:
            try:
                self.app.db.update_inventory_item(
                    self.editing_item_id,
                    name=name,
                    quantity_base=quantity_base,
                    display_unit=unit,
                    base_unit=base_unit,
                    conversion_to_base=conversion,
                    low_stock_threshold_base=threshold_base,
                )
            except Exception as exc:  # pragma: no cover - Tkinter UI guard
                messagebox.showerror("Error", f"Could not update item: {exc}")
                return
        self.refresh_inventory()
        vendor_frame: VendorOrdersFrame = self.app.frames[VendorOrdersFrame]  # type: ignore[assignment]
        vendor_frame.reload_sources()

    def delete_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Select an item to delete")
            return
        item_id = int(selection[0])
        if messagebox.askyesno("Confirm", "Remove the selected inventory item?"):
            self.app.db.delete_inventory_item(item_id)
            self.refresh_inventory()
            vendor_frame: VendorOrdersFrame = self.app.frames[VendorOrdersFrame]  # type: ignore[assignment]
            vendor_frame.reload_sources()

    def apply_theme(self, palette: Dict[str, str]) -> None:
        self.low_stock_label.configure(foreground=palette["warning"])


class InventoryEditFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=2)
        wrapper.columnconfigure(1, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Edit inventory", font=get_font(22, "bold")).pack(side=tk.LEFT)
        nav_bar = ttk.Frame(header)
        nav_bar.pack(side=tk.RIGHT)
        self.add_nav_buttons(nav_bar)

        self.tree = ttk.Treeview(
            wrapper,
            columns=("quantity", "unit", "threshold"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.tree.heading("#0", text="Item")
        self.tree.column("#0", width=200, anchor=tk.W)
        self.tree.heading("quantity", text="On hand")
        self.tree.heading("unit", text="Unit")
        self.tree.heading("threshold", text="Low stock at")
        self.tree.column("quantity", width=120, anchor=tk.CENTER)
        self.tree.column("unit", width=80, anchor=tk.CENTER)
        self.tree.column("threshold", width=140, anchor=tk.CENTER)
        self.tree.bind("<<TreeviewSelect>>", lambda _: self.load_selected())

        form = ttk.LabelFrame(wrapper, text="Adjust selection", padding=15)
        form.grid(row=1, column=1, sticky="nsew", padx=(20, 0), pady=(20, 0))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Item:").grid(row=0, column=0, sticky="e", pady=4)
        self.item_name_var = tk.StringVar()
        ttk.Label(form, textvariable=self.item_name_var, font=get_font(11, "bold")).grid(
            row=0, column=1, sticky="w"
        )

        ttk.Label(form, text="Current quantity:").grid(row=1, column=0, sticky="e", pady=4)
        self.current_quantity_var = tk.StringVar(value="-")
        ttk.Label(form, textvariable=self.current_quantity_var).grid(row=1, column=1, sticky="w")

        ttk.Label(form, text="Adjust by:").grid(row=2, column=0, sticky="e", pady=4)
        self.adjustment_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.adjustment_var).grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Use negative value to deduct.").grid(row=3, column=0, columnspan=2, sticky="w")

        ttk.Label(form, text="New threshold:").grid(row=4, column=0, sticky="e", pady=4)
        self.threshold_edit_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.threshold_edit_var).grid(row=4, column=1, sticky="ew", pady=4)

        button_bar = ttk.Frame(form)
        button_bar.grid(row=5, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(button_bar, text="Apply adjustment", command=self.apply_adjustment).grid(row=0, column=0, padx=5)
        ttk.Button(button_bar, text="Update threshold", command=self.update_threshold).grid(row=0, column=1, padx=5)

        ttk.Button(form, text="Delete item", command=self.delete_item).grid(
            row=6, column=0, columnspan=2, pady=(12, 0), sticky="ew"
        )

        self.selected_item_id: Optional[int] = None
        self.selected_conversion: float = 1.0

    def on_show(self, **_: object) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.app.db.get_inventory_items():
            self.tree.insert(
                "",
                tk.END,
                iid=str(item.id),
                text=item.name,
                values=(
                    format_quantity(item.quantity_base, item.conversion_to_base),
                    item.display_unit,
                    format_quantity(item.low_stock_threshold_base, item.conversion_to_base),
                ),
            )
        self.clear_selection()

    def clear_selection(self) -> None:
        self.selected_item_id = None
        self.selected_conversion = 1.0
        self.item_name_var.set("Select an item")
        self.current_quantity_var.set("-")
        self.adjustment_var.set("")
        self.threshold_edit_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def load_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        item_id = int(selection[0])
        inventory_item = self.app.db.get_inventory_item(item_id)
        if inventory_item is None:
            return
        self.selected_item_id = item_id
        self.selected_conversion = inventory_item.conversion_to_base
        self.item_name_var.set(inventory_item.name)
        self.current_quantity_var.set(
            f"{format_quantity(inventory_item.quantity_base, inventory_item.conversion_to_base)} {inventory_item.display_unit}"
        )
        self.threshold_edit_var.set(
            format_quantity(inventory_item.low_stock_threshold_base, inventory_item.conversion_to_base)
        )

    def apply_adjustment(self) -> None:
        if self.selected_item_id is None:
            messagebox.showinfo("Select item", "Choose an inventory item first")
            return
        try:
            adjustment_display = float(self.adjustment_var.get())
        except ValueError:
            messagebox.showerror("Invalid value", "Enter a numeric adjustment")
            return
        delta_base = adjustment_display * self.selected_conversion
        self.app.db.adjust_inventory(self.selected_item_id, delta_base)
        self.refresh_items()
        inventory_frame: InventoryFrame = self.app.frames[InventoryFrame]  # type: ignore[assignment]
        inventory_frame.refresh_inventory()
        dashboard: DashboardFrame = self.app.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.refresh_status()

    def update_threshold(self) -> None:
        if self.selected_item_id is None:
            messagebox.showinfo("Select item", "Choose an inventory item first")
            return
        try:
            threshold_display = float(self.threshold_edit_var.get())
        except ValueError:
            messagebox.showerror("Invalid value", "Enter a numeric threshold")
            return
        threshold_base = threshold_display * self.selected_conversion
        self.app.db.update_inventory_item(self.selected_item_id, low_stock_threshold_base=threshold_base)
        self.refresh_items()
        inventory_frame: InventoryFrame = self.app.frames[InventoryFrame]  # type: ignore[assignment]
        inventory_frame.refresh_inventory()
        dashboard: DashboardFrame = self.app.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.refresh_status()

    def delete_item(self) -> None:
        if self.selected_item_id is None:
            messagebox.showinfo("Select item", "Choose an inventory item first")
            return
        if not messagebox.askyesno("Confirm", "Delete the selected inventory item?"):
            return
        self.app.db.delete_inventory_item(self.selected_item_id)
        self.refresh_items()
        inventory_frame: InventoryFrame = self.app.frames[InventoryFrame]  # type: ignore[assignment]
        inventory_frame.refresh_inventory()
        dashboard: DashboardFrame = self.app.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.refresh_status()


class RecipeFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.columnconfigure(1, weight=2)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Recipes", font=get_font(22, "bold")).pack(side=tk.LEFT)
        nav_bar = ttk.Frame(header)
        nav_bar.pack(side=tk.RIGHT)
        self.add_nav_buttons(nav_bar)

        self.recipe_tree = ttk.Treeview(wrapper, columns=("count",), show="tree")
        self.recipe_tree.heading("#0", text="Recipe")
        self.recipe_tree.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.recipe_tree.bind("<<TreeviewSelect>>", lambda _: self.load_recipe_details())

        controls = ttk.Frame(wrapper)
        controls.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        ttk.Button(controls, text="Add recipe", command=self.open_add_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Delete recipe", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Start cooking", command=self.start_cooking).pack(side=tk.LEFT, padx=5)

        detail_panel = ttk.Frame(wrapper, padding=20, relief=tk.GROOVE)
        detail_panel.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=(20, 0), pady=(20, 0))
        detail_panel.columnconfigure(0, weight=1)
        detail_panel.rowconfigure(4, weight=1)

        self.detail_name = tk.StringVar()
        ttk.Label(detail_panel, textvariable=self.detail_name, font=get_font(18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.detail_description = tk.StringVar()
        ttk.Label(detail_panel, textvariable=self.detail_description, wraplength=420, justify=tk.LEFT).grid(
            row=1, column=0, sticky="w", pady=(10, 20)
        )

        ingredients_frame = ttk.LabelFrame(detail_panel, text="Ingredients", padding=10)
        ingredients_frame.grid(row=2, column=0, sticky="nsew")
        self.ingredients_list = tk.Listbox(ingredients_frame, height=6, highlightthickness=0, borderwidth=0)
        self.ingredients_list.pack(fill=tk.BOTH, expand=True)

        steps_frame = ttk.LabelFrame(detail_panel, text="Steps", padding=10)
        steps_frame.grid(row=3, column=0, sticky="nsew", pady=(20, 0))
        self.steps_list = tk.Listbox(steps_frame, height=8, highlightthickness=0, borderwidth=0)
        self.steps_list.pack(fill=tk.BOTH, expand=True)

        self.selected_recipe_id: Optional[int] = None

        self.register_theme_observer(self.apply_theme)

    def on_show(self, **_: object) -> None:
        self.refresh_recipes()

    def refresh_recipes(self) -> None:
        for row in self.recipe_tree.get_children():
            self.recipe_tree.delete(row)
        for recipe in self.app.db.get_recipes():
            self.recipe_tree.insert("", tk.END, iid=str(recipe.id), text=recipe.name)
        self.selected_recipe_id = None
        self.detail_name.set("Select a recipe to view details")
        self.detail_description.set("")
        self.ingredients_list.delete(0, tk.END)
        self.steps_list.delete(0, tk.END)

    def load_recipe_details(self) -> None:
        selection = self.recipe_tree.selection()
        if not selection:
            return
        recipe_id = int(selection[0])
        recipe = next((r for r in self.app.db.get_recipes() if r.id == recipe_id), None)
        if recipe is None:
            return
        self.selected_recipe_id = recipe_id
        self.detail_name.set(recipe.name)
        self.detail_description.set(recipe.description)
        self.ingredients_list.delete(0, tk.END)
        for ingredient in self.app.db.get_recipe_ingredients(recipe_id):
            item = self.app.db.get_inventory_item(ingredient.inventory_item_id)
            if item:
                amount = format_quantity(ingredient.quantity_base, item.conversion_to_base)
                self.ingredients_list.insert(tk.END, f"{item.name}: {amount} {item.display_unit}")
        self.steps_list.delete(0, tk.END)
        for step in self.app.db.get_recipe_steps(recipe_id):
            self.steps_list.insert(tk.END, f"{step.position}. {step.instruction}")

    def open_add_dialog(self) -> None:
        dialog = RecipeDialog(self, self.app.db)
        self.wait_window(dialog)
        self.refresh_recipes()

    def delete_selected(self) -> None:
        selection = self.recipe_tree.selection()
        if not selection:
            messagebox.showinfo("Select recipe", "Please choose a recipe to delete")
            return
        recipe_id = int(selection[0])
        if messagebox.askyesno("Confirm", "Delete the selected recipe?"):
            self.app.db.delete_recipe(recipe_id)
            self.refresh_recipes()

    def start_cooking(self) -> None:
        if self.selected_recipe_id is None:
            messagebox.showinfo("Select recipe", "Choose a recipe to start cooking")
            return
        recipe_id = self.selected_recipe_id
        ingredients = self.app.db.get_recipe_ingredients(recipe_id)
        if not ingredients:
            messagebox.showerror("Missing ingredients", "This recipe has no ingredients defined")
            return
        usage, missing = compute_recipe_usage(self.app.db, recipe_id)
        if missing:
            messagebox.showerror(
                "Insufficient stock",
                "Cannot start cooking because:\n" + "\n".join(missing),
            )
            return
        steps = self.app.db.get_recipe_steps(recipe_id)
        if not steps:
            messagebox.showerror("Missing steps", "Please define steps for this recipe before cooking")
            return
        CookingDialog(self, recipe_id, steps, usage)

    def apply_theme(self, palette: Dict[str, str]) -> None:
        for widget in (self.ingredients_list, self.steps_list):
            widget.configure(
                bg=palette["surface"],
                fg=palette["text"],
                selectbackground=palette["accent"],
                selectforeground=palette["on_accent"],
                highlightbackground=palette["border"],
                highlightcolor=palette["border"],
            )


class RecipeDialog(tk.Toplevel):
    def __init__(self, parent: RecipeFrame, db: DatabaseManager) -> None:
        super().__init__(parent)
        self.title("Add recipe")
        self.resizable(False, False)
        self.db = db
        self.transient(parent)
        self.grab_set()

        self.columnconfigure(0, weight=1)

        palette = parent.app.current_palette or THEME_PALETTES["Light"]
        self.configure(bg=palette["background"])

        ttk.Label(self, text="Recipe name:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, width=40).grid(row=1, column=0, padx=10, sticky="ew")

        ttk.Label(self, text="Description (optional):").grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))
        self.description_text = tk.Text(self, width=50, height=4, highlightthickness=0, borderwidth=0)
        self.description_text.grid(row=3, column=0, padx=10, sticky="ew")

        ingredient_frame = ttk.LabelFrame(self, text="Ingredients", padding=10)
        ingredient_frame.grid(row=4, column=0, padx=10, pady=(15, 0), sticky="ew")
        ingredient_frame.columnconfigure(1, weight=1)

        ttk.Label(ingredient_frame, text="Inventory item:").grid(row=0, column=0, sticky="w")
        self.inventory_map = {item.name: item for item in db.get_inventory_items()}
        if not self.inventory_map:
            messagebox.showerror(
                "Add inventory first",
                "Please capture inventory items before creating recipes.",
            )
            self.destroy()
            return
        self.ingredient_item_var = tk.StringVar()
        self.ingredient_select = ttk.Combobox(
            ingredient_frame,
            textvariable=self.ingredient_item_var,
            state="readonly",
            values=list(self.inventory_map.keys()),
            width=25,
        )
        self.ingredient_select.grid(row=1, column=0, sticky="ew", pady=5)

        ttk.Label(ingredient_frame, text="Quantity:").grid(row=0, column=1, sticky="w")
        self.ingredient_quantity = tk.StringVar()
        ttk.Entry(ingredient_frame, textvariable=self.ingredient_quantity).grid(row=1, column=1, sticky="ew", pady=5)

        ingredient_buttons = ttk.Frame(ingredient_frame)
        ingredient_buttons.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        ttk.Button(ingredient_buttons, text="Add ingredient", command=self.add_ingredient).pack(side=tk.LEFT, padx=5)
        ttk.Button(ingredient_buttons, text="Remove selected", command=self.remove_selected).pack(side=tk.LEFT, padx=5)

        self.ingredients_tree = ttk.Treeview(ingredient_frame, columns=("quantity", "unit"), show="headings", height=5)
        self.ingredients_tree.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.ingredients_tree.heading("quantity", text="Quantity")
        self.ingredients_tree.heading("unit", text="Unit")

        ttk.Label(self, text="Steps (one per line):").grid(row=5, column=0, sticky="w", padx=10, pady=(15, 0))
        self.steps_text = tk.Text(self, width=50, height=8, highlightthickness=0, borderwidth=0)
        self.steps_text.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="ew")

        button_bar = ttk.Frame(self)
        button_bar.grid(row=7, column=0, pady=10)
        ttk.Button(button_bar, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_bar, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.ingredients: List[tuple[int, float]] = []

        for widget in (self.description_text, self.steps_text):
            widget.configure(
                bg=palette["surface"],
                fg=palette["text"],
                insertbackground=palette["text"],
                highlightbackground=palette["border"],
                highlightcolor=palette["border"],
            )

    def add_ingredient(self) -> None:
        item_name = self.ingredient_item_var.get()
        if not item_name:
            messagebox.showerror("Select item", "Choose an inventory item to add")
            return
        try:
            amount = float(self.ingredient_quantity.get())
        except ValueError:
            messagebox.showerror("Invalid quantity", "Enter a numeric quantity")
            return
        inventory_item = self.inventory_map[item_name]
        if any(inv_id == inventory_item.id for inv_id, _ in self.ingredients):
            messagebox.showerror("Duplicate ingredient", "This ingredient is already listed")
            return
        quantity_base = amount * inventory_item.conversion_to_base
        self.ingredients.append((inventory_item.id, quantity_base))
        self.ingredients_tree.insert(
            "",
            tk.END,
            iid=f"{inventory_item.id}-{len(self.ingredients)}",
            values=(f"{amount:.2f}", inventory_item.display_unit),
        )
        self.ingredient_quantity.set("")

    def remove_selected(self) -> None:
        selection = self.ingredients_tree.selection()
        if not selection:
            return
        index = self.ingredients_tree.index(selection[0])
        self.ingredients_tree.delete(selection[0])
        if 0 <= index < len(self.ingredients):
            self.ingredients.pop(index)

    def save(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Recipe name is required")
            return
        if not self.ingredients:
            messagebox.showerror("Missing ingredients", "Add at least one ingredient")
            return
        steps = [line.strip() for line in self.steps_text.get("1.0", tk.END).splitlines() if line.strip()]
        if not steps:
            messagebox.showerror("Missing steps", "Enter at least one step")
            return
        description = self.description_text.get("1.0", tk.END).strip()
        try:
            self.db.add_recipe(name, description, self.ingredients, steps)
        except Exception as exc:  # pragma: no cover - Tkinter UI guard
            messagebox.showerror("Error", f"Could not save recipe: {exc}")
            return
        self.destroy()


class CookingDialog(tk.Toplevel):
    def __init__(
        self,
        parent: RecipeFrame,
        recipe_id: int,
        steps: List[RecipeStep],
        usage: List[tuple[int, float]],
    ) -> None:
        super().__init__(parent)
        self.title("Cooking checklist")
        self.resizable(False, False)
        self.parent = parent
        self.recipe_id = recipe_id
        self.usage = usage
        self.steps = steps
        self.completed = False
        self.transient(parent)
        self.grab_set()

        palette = parent.app.current_palette or THEME_PALETTES["Light"]
        self.configure(bg=palette["background"])

        ttk.Label(self, text="Tick steps as you progress", font=get_font(14, "bold")).pack(pady=(15, 10))
        self.step_vars: List[tk.BooleanVar] = []
        for step in steps:
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(self, text=f"{step.position}. {step.instruction}", variable=var, command=self.check_done)
            chk.pack(anchor="w", padx=20, pady=4)
            self.step_vars.append(var)

        ttk.Button(self, text="Cancel", command=self.cancel).pack(pady=(10, 15))

    def check_done(self) -> None:
        if self.completed:
            return
        if all(var.get() for var in self.step_vars):
            self.completed = True
            for item_id, qty in self.usage:
                self.parent.app.db.adjust_inventory(item_id, -qty)
            self.parent.app.db.record_cooking_session(self.recipe_id, self.usage)
            messagebox.showinfo("Recipe completed", "Recipe completed")
            self.parent.refresh_recipes()
            inventory_frame: InventoryFrame = self.parent.app.frames[InventoryFrame]  # type: ignore[assignment]
            inventory_frame.refresh_inventory()
            self.destroy()

    def cancel(self) -> None:
        self.destroy()


class SuppliersFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=2)
        wrapper.columnconfigure(1, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Suppliers", font=get_font(22, "bold")).pack(side=tk.LEFT)
        nav = ttk.Frame(header)
        nav.pack(side=tk.RIGHT)
        self.add_nav_buttons(nav)

        self.tree = ttk.Treeview(
            wrapper,
            columns=("contact", "phone", "email", "notes"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Supplier")
        for col, heading, width in (
            ("contact", "Contact", 140),
            ("phone", "Phone", 120),
            ("email", "Email", 180),
            ("notes", "Notes", 200),
        ):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=tk.W)
        self.tree.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.tree.bind("<<TreeviewSelect>>", lambda _: self.load_selected())

        form = ttk.LabelFrame(wrapper, text="Supplier details", padding=15)
        form.grid(row=1, column=1, sticky="nsew", padx=(20, 0), pady=(20, 0))
        form.columnconfigure(1, weight=1)

        self.supplier_name = tk.StringVar()
        self.contact_person = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        ttk.Label(form, text="Name:").grid(row=0, column=0, sticky="e", pady=4)
        ttk.Entry(form, textvariable=self.supplier_name).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Contact person:").grid(row=1, column=0, sticky="e", pady=4)
        ttk.Entry(form, textvariable=self.contact_person).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Phone:").grid(row=2, column=0, sticky="e", pady=4)
        ttk.Entry(form, textvariable=self.phone_var).grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Email:").grid(row=3, column=0, sticky="e", pady=4)
        ttk.Entry(form, textvariable=self.email_var).grid(row=3, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Notes:").grid(row=4, column=0, sticky="ne", pady=4)
        ttk.Entry(form, textvariable=self.notes_var).grid(row=4, column=1, sticky="ew", pady=4)

        button_bar = ttk.Frame(form)
        button_bar.grid(row=5, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(button_bar, text="Save supplier", command=self.save_supplier).grid(row=0, column=0, padx=5)
        ttk.Button(button_bar, text="Reset", command=self.reset_form).grid(row=0, column=1, padx=5)
        ttk.Button(form, text="Delete supplier", command=self.delete_supplier).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0)
        )

        self.editing_id: Optional[int] = None
        self.supplier_cache: Dict[int, Supplier] = {}

    def on_show(self, **_: object) -> None:
        self.refresh_suppliers()

    def refresh_suppliers(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        suppliers = self.app.db.get_suppliers()
        self.supplier_cache = {supplier.id: supplier for supplier in suppliers}
        for supplier in suppliers:
            self.tree.insert(
                "",
                tk.END,
                iid=str(supplier.id),
                text=supplier.name,
                values=(supplier.contact_person, supplier.phone, supplier.email, supplier.notes),
            )
        self.reset_form(clear_selection=False)

    def reset_form(self, *, clear_selection: bool = True) -> None:
        self.editing_id = None
        self.supplier_name.set("")
        self.contact_person.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.notes_var.set("")
        if clear_selection:
            self.tree.selection_remove(self.tree.selection())

    def load_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        supplier_id = int(selection[0])
        supplier = self.supplier_cache.get(supplier_id)
        if supplier is None:
            return
        self.editing_id = supplier.id
        self.supplier_name.set(supplier.name)
        self.contact_person.set(supplier.contact_person)
        self.phone_var.set(supplier.phone)
        self.email_var.set(supplier.email)
        self.notes_var.set(supplier.notes)

    def save_supplier(self) -> None:
        name = self.supplier_name.get().strip()
        if not name:
            messagebox.showerror("Missing name", "Supplier name is required")
            return
        details = dict(
            contact_person=self.contact_person.get().strip(),
            phone=self.phone_var.get().strip(),
            email=self.email_var.get().strip(),
            notes=self.notes_var.get().strip(),
        )
        if self.editing_id is None:
            self.app.db.add_supplier(name, **details)
        else:
            self.app.db.update_supplier(self.editing_id, name=name, **details)
        self.refresh_suppliers()
        vendor_frame: VendorOrdersFrame = self.app.frames[VendorOrdersFrame]  # type: ignore[assignment]
        vendor_frame.reload_sources()

    def delete_supplier(self) -> None:
        if self.editing_id is None:
            messagebox.showinfo("Select supplier", "Choose a supplier to delete")
            return
        if not messagebox.askyesno("Confirm", "Remove the selected supplier?"):
            return
        self.app.db.delete_supplier(self.editing_id)
        self.refresh_suppliers()
        vendor_frame: VendorOrdersFrame = self.app.frames[VendorOrdersFrame]  # type: ignore[assignment]
        vendor_frame.reload_sources()


class VendorOrdersFrame(BaseFrame):
    STATUSES = ("Pending", "Ordered", "Received")

    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Vendor orders", font=get_font(22, "bold")).pack(side=tk.LEFT)
        nav = ttk.Frame(header)
        nav.pack(side=tk.RIGHT)
        self.add_nav_buttons(nav)

        self.tree = ttk.Treeview(
            wrapper,
            columns=("supplier", "item", "quantity", "status", "ordered", "expected", "received"),
            show="headings",
            height=12,
        )
        headings = [
            ("supplier", "Supplier", 160),
            ("item", "Item", 160),
            ("quantity", "Quantity", 110),
            ("status", "Status", 100),
            ("ordered", "Ordered at", 150),
            ("expected", "Expected", 120),
            ("received", "Received", 150),
        ]
        for col, heading, width in headings:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=tk.CENTER if col == "quantity" else tk.W)
        self.tree.grid(row=1, column=0, sticky="nsew", pady=(20, 0))

        form = ttk.LabelFrame(wrapper, text="Create order", padding=15)
        form.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        form.columnconfigure(1, weight=1)

        self.supplier_var = tk.StringVar()
        self.item_var = tk.StringVar()
        self.quantity_var = tk.StringVar()
        self.order_status_var = tk.StringVar(value="Pending")
        self.expected_var = tk.StringVar()

        ttk.Label(form, text="Supplier:").grid(row=0, column=0, sticky="e", pady=4)
        self.supplier_combo = ttk.Combobox(form, textvariable=self.supplier_var, state="readonly")
        self.supplier_combo.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Item:").grid(row=1, column=0, sticky="e", pady=4)
        self.item_combo = ttk.Combobox(form, textvariable=self.item_var, state="readonly")
        self.item_combo.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Quantity (display unit):").grid(row=2, column=0, sticky="e", pady=4)
        ttk.Entry(form, textvariable=self.quantity_var).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Status:").grid(row=3, column=0, sticky="e", pady=4)
        status_combo = ttk.Combobox(form, textvariable=self.order_status_var, state="readonly", values=self.STATUSES)
        status_combo.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Expected date (optional):").grid(row=4, column=0, sticky="e", pady=4)
        ttk.Entry(form, textvariable=self.expected_var).grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Button(form, text="Create order", command=self.create_order).grid(row=5, column=0, columnspan=2, pady=(12, 0))

        action_bar = ttk.Frame(wrapper)
        action_bar.grid(row=3, column=0, sticky="ew", pady=(20, 0))
        ttk.Button(action_bar, text="Mark as ordered", command=lambda: self.mark_status("Ordered")).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="Mark as received", command=self.receive_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="Delete order", command=self.delete_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="Refresh", command=self.refresh_orders).pack(side=tk.LEFT, padx=5)

        self.supplier_map: Dict[str, int] = {}
        self.item_map: Dict[str, tuple[int, float, str]] = {}
        self.order_cache: Dict[int, VendorOrder] = {}

    def on_show(self, **_: object) -> None:
        self.reload_sources()
        self.refresh_orders()

    def reload_sources(self) -> None:
        self.supplier_map = {supplier.name: supplier.id for supplier in self.app.db.get_suppliers()}
        self.item_map = {
            item.name: (item.id, item.conversion_to_base, item.display_unit)
            for item in self.app.db.get_inventory_items()
        }
        self.supplier_combo["values"] = list(self.supplier_map.keys())
        self.item_combo["values"] = list(self.item_map.keys())
        if not self.supplier_map:
            self.supplier_var.set("")
        if not self.item_map:
            self.item_var.set("")

    def refresh_orders(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.order_cache = {}
        for order in self.app.db.get_vendor_orders():
            quantity_display = format_quantity(order.quantity_base, order.conversion_to_base)
            self.tree.insert(
                "",
                tk.END,
                iid=str(order.id),
                values=(
                    order.supplier_name,
                    order.inventory_item_name,
                    f"{quantity_display} {order.display_unit}",
                    order.status,
                    order.ordered_at.split("T")[0],
                    order.expected_date or "-",
                    (order.received_at.split("T")[0] if order.received_at else "-"),
                ),
            )
            self.order_cache[order.id] = order
        dashboard: DashboardFrame = self.app.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.refresh_status()

    def get_selected_order(self) -> Optional[VendorOrder]:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select order", "Choose an order first")
            return None
        order_id = int(selection[0])
        return self.order_cache.get(order_id)

    def create_order(self) -> None:
        supplier_name = self.supplier_var.get()
        item_name = self.item_var.get()
        if not supplier_name or supplier_name not in self.supplier_map:
            messagebox.showerror("Missing supplier", "Select a supplier")
            return
        if not item_name or item_name not in self.item_map:
            messagebox.showerror("Missing item", "Select an inventory item")
            return
        try:
            quantity_display = float(self.quantity_var.get())
        except ValueError:
            messagebox.showerror("Invalid quantity", "Enter a numeric quantity")
            return
        item_id, conversion, _ = self.item_map[item_name]
        quantity_base = quantity_display * conversion
        expected_date = self.expected_var.get().strip() or None
        status = self.order_status_var.get() or "Pending"
        order_id = self.app.db.add_vendor_order(
            self.supplier_map[supplier_name],
            item_id,
            quantity_base,
            status=status,
            expected_date=expected_date,
        )
        if status == "Received":
            self.app.db.receive_vendor_order(order_id)
        self.quantity_var.set("")
        self.expected_var.set("")
        self.refresh_orders()

    def mark_status(self, status: str) -> None:
        order = self.get_selected_order()
        if order is None:
            return
        if order.status == "Received":
            messagebox.showinfo("Already received", "This order has already been received")
            return
        self.app.db.update_vendor_order_status(order.id, status)
        self.refresh_orders()

    def receive_selected(self) -> None:
        order = self.get_selected_order()
        if order is None:
            return
        self.app.db.receive_vendor_order(order.id)
        self.refresh_orders()
        inventory_frame: InventoryFrame = self.app.frames[InventoryFrame]  # type: ignore[assignment]
        inventory_frame.refresh_inventory()

    def delete_order(self) -> None:
        order = self.get_selected_order()
        if order is None:
            return
        if not messagebox.askyesno("Confirm", "Delete the selected vendor order?"):
            return
        self.app.db.delete_vendor_order(order.id)
        self.refresh_orders()


class CustomerOrdersFrame(BaseFrame):
    STATUSES = ("Pending", "In Progress", "Completed", "Cancelled")

    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Customer orders", font=get_font(22, "bold")).pack(side=tk.LEFT)
        nav = ttk.Frame(header)
        nav.pack(side=tk.RIGHT)
        self.add_nav_buttons(nav)

        self.tree = ttk.Treeview(
            wrapper,
            columns=("customer", "recipe", "servings", "status", "created"),
            show="headings",
        )
        for col, heading, width in (
            ("customer", "Customer", 160),
            ("recipe", "Recipe", 160),
            ("servings", "Servings", 90),
            ("status", "Status", 120),
            ("created", "Created", 150),
        ):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=tk.CENTER if col == "servings" else tk.W)
        self.tree.grid(row=1, column=0, sticky="nsew", pady=(20, 0))

        form = ttk.LabelFrame(wrapper, text="Log customer order", padding=15)
        form.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        form.columnconfigure(1, weight=1)

        self.customer_var = tk.StringVar()
        self.recipe_var = tk.StringVar()
        self.servings_var = tk.StringVar(value="1")

        ttk.Label(form, text="Customer name:").grid(row=0, column=0, sticky="e", pady=4)
        ttk.Entry(form, textvariable=self.customer_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Recipe:").grid(row=1, column=0, sticky="e", pady=4)
        self.recipe_combo = ttk.Combobox(form, textvariable=self.recipe_var, state="readonly")
        self.recipe_combo.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Servings:").grid(row=2, column=0, sticky="e", pady=4)
        ttk.Entry(form, textvariable=self.servings_var).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Button(form, text="Add order", command=self.add_order).grid(row=3, column=0, columnspan=2, pady=(12, 0))

        action_bar = ttk.Frame(wrapper)
        action_bar.grid(row=3, column=0, sticky="ew", pady=(20, 0))
        ttk.Button(action_bar, text="Set in progress", command=lambda: self.update_status("In Progress")).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="Complete order", command=self.complete_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="Cancel order", command=lambda: self.update_status("Cancelled")).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="Delete", command=self.delete_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_bar, text="Refresh", command=self.refresh_orders).pack(side=tk.LEFT, padx=5)

        self.recipe_map: Dict[str, int] = {}
        self.orders: Dict[int, CustomerOrder] = {}

    def on_show(self, **_: object) -> None:
        self.reload_sources()
        self.refresh_orders()

    def reload_sources(self) -> None:
        self.recipe_map = {recipe.name: recipe.id for recipe in self.app.db.get_recipes()}
        self.recipe_combo["values"] = list(self.recipe_map.keys())
        if not self.recipe_map:
            self.recipe_var.set("")

    def refresh_orders(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.orders = {}
        for order in self.app.db.get_customer_orders():
            self.tree.insert(
                "",
                tk.END,
                iid=str(order.id),
                values=(
                    order.customer_name,
                    order.recipe_name,
                    order.servings,
                    order.status,
                    order.created_at.split("T")[0],
                ),
            )
            self.orders[order.id] = order
        dashboard: DashboardFrame = self.app.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.refresh_status()

    def get_selected(self) -> Optional[CustomerOrder]:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select order", "Choose an order first")
            return None
        order_id = int(selection[0])
        return self.orders.get(order_id)

    def add_order(self) -> None:
        customer = self.customer_var.get().strip()
        recipe_name = self.recipe_var.get()
        if not customer:
            messagebox.showerror("Missing customer", "Enter the customer's name")
            return
        if recipe_name not in self.recipe_map:
            messagebox.showerror("Missing recipe", "Select a recipe")
            return
        try:
            servings = int(self.servings_var.get())
        except ValueError:
            messagebox.showerror("Invalid servings", "Servings must be a whole number")
            return
        if servings <= 0:
            messagebox.showerror("Invalid servings", "Servings must be positive")
            return
        self.app.db.add_customer_order(customer, self.recipe_map[recipe_name], servings)
        self.customer_var.set("")
        self.servings_var.set("1")
        self.refresh_orders()

    def update_status(self, status: str) -> None:
        order = self.get_selected()
        if order is None:
            return
        if order.status == "Completed" and status != "Completed":
            messagebox.showinfo("Already completed", "This order is already complete")
            return
        self.app.db.update_customer_order_status(order.id, status)
        self.refresh_orders()

    def complete_order(self) -> None:
        order = self.get_selected()
        if order is None:
            return
        if order.status == "Completed":
            messagebox.showinfo("Already completed", "This order is already marked complete")
            return
        steps = self.app.db.get_recipe_steps(order.recipe_id)
        if not steps:
            messagebox.showerror("Missing steps", "This recipe has no steps defined")
            return
        usage, missing = compute_recipe_usage(self.app.db, order.recipe_id, multiplier=float(order.servings))
        if missing:
            messagebox.showerror(
                "Insufficient stock",
                "Cannot complete the order because:\n" + "\n".join(missing),
            )
            return
        for item_id, qty in usage:
            self.app.db.adjust_inventory(item_id, -qty)
        self.app.db.record_cooking_session(order.recipe_id, usage)
        self.app.db.update_customer_order_status(order.id, "Completed")
        inventory_frame: InventoryFrame = self.app.frames[InventoryFrame]  # type: ignore[assignment]
        inventory_frame.refresh_inventory()
        self.refresh_orders()

    def delete_order(self) -> None:
        order = self.get_selected()
        if order is None:
            return
        if not messagebox.askyesno("Confirm", "Delete the selected customer order?"):
            return
        self.app.db.delete_customer_order(order.id)
        self.refresh_orders()


class SettingsFrame(BaseFrame):
    DEFAULTS = {
        "restaurant_name": "KitchenMate",
        "notification_email": "",
        "default_lead_days": "2",
        "theme": "Light",
    }

    LABELS = {
        "restaurant_name": "Restaurant name",
        "notification_email": "Notification email",
        "default_lead_days": "Default vendor lead time (days)",
        "theme": "Theme preference",
    }

    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Settings", font=get_font(22, "bold")).pack(side=tk.LEFT)
        nav = ttk.Frame(header)
        nav.pack(side=tk.RIGHT)
        self.add_nav_buttons(nav)

        form = ttk.LabelFrame(wrapper, text="Application preferences", padding=20)
        form.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        form.columnconfigure(1, weight=1)

        self.setting_vars: Dict[str, tk.StringVar] = {}
        self.setting_inputs: Dict[str, tk.Widget] = {}
        for idx, (key, label) in enumerate(self.LABELS.items()):
            ttk.Label(form, text=f"{label}:").grid(row=idx, column=0, sticky="e", pady=6, padx=(0, 12))
            var = tk.StringVar()
            if key == "theme":
                input_widget: tk.Widget = ttk.Combobox(
                    form,
                    textvariable=var,
                    values=self.app.available_themes,
                    state="readonly",
                )
            else:
                input_widget = ttk.Entry(form, textvariable=var)
            input_widget.grid(row=idx, column=1, sticky="ew", pady=6)
            self.setting_vars[key] = var
            self.setting_inputs[key] = input_widget

        button_bar = ttk.Frame(form)
        button_bar.grid(row=len(self.LABELS), column=0, columnspan=2, pady=(20, 0))
        ttk.Button(button_bar, text="Save settings", command=self.save_settings).grid(row=0, column=0, padx=5)
        ttk.Button(button_bar, text="Reset to defaults", command=self.reset_defaults).grid(row=0, column=1, padx=5)

    def on_show(self, **_: object) -> None:
        self.load_settings()

    def load_settings(self) -> None:
        stored = self.app.db.get_all_settings()
        for key, var in self.setting_vars.items():
            value = stored.get(key, self.DEFAULTS.get(key, ""))
            if key == "theme" and value not in self.app.available_themes:
                value = self.DEFAULTS["theme"]
            var.set(value)

    def save_settings(self) -> None:
        for key, var in self.setting_vars.items():
            value = var.get()
            if key != "theme":
                value = value.strip()
            self.app.db.set_setting(key, value)
        self.app.apply_theme(self.setting_vars["theme"].get())
        messagebox.showinfo("Settings saved", "Preferences updated successfully")
        dashboard: DashboardFrame = self.app.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.refresh_status()

    def reset_defaults(self) -> None:
        for key, default in self.DEFAULTS.items():
            if key in self.setting_vars:
                self.setting_vars[key].set(default)
                self.app.db.set_setting(key, default)
        self.app.apply_theme(self.setting_vars["theme"].get())
        dashboard: DashboardFrame = self.app.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.refresh_status()


class ReportsFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.columnconfigure(1, weight=1)
        wrapper.rowconfigure(1, weight=1)
        wrapper.rowconfigure(2, weight=1)
        wrapper.rowconfigure(3, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Reports", font=get_font(22, "bold")).pack(side=tk.LEFT)
        nav_bar = ttk.Frame(header)
        nav_bar.pack(side=tk.RIGHT)
        self.add_nav_buttons(nav_bar)

        recipe_frame = ttk.LabelFrame(wrapper, text="Recipe popularity", padding=15)
        recipe_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(20, 0))
        self.recipe_report = ttk.Treeview(
            recipe_frame,
            columns=("recipe", "count"),
            show="headings",
            height=8,
        )
        self.recipe_report.heading("recipe", text="Recipe")
        self.recipe_report.heading("count", text="Times cooked")
        self.recipe_report.column("recipe", anchor=tk.W, width=220)
        self.recipe_report.column("count", anchor=tk.CENTER, width=120)
        self.recipe_report.pack(fill=tk.BOTH, expand=True)

        usage_frame = ttk.LabelFrame(wrapper, text="Ingredient usage", padding=15)
        usage_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(20, 0))
        self.usage_report = ttk.Treeview(
            usage_frame,
            columns=("ingredient", "used", "unit"),
            show="headings",
            height=8,
        )
        self.usage_report.heading("ingredient", text="Ingredient")
        self.usage_report.heading("used", text="Quantity used")
        self.usage_report.heading("unit", text="Unit")
        self.usage_report.column("ingredient", anchor=tk.W, width=220)
        self.usage_report.column("used", anchor=tk.CENTER, width=140)
        self.usage_report.column("unit", anchor=tk.CENTER, width=80)
        self.usage_report.pack(fill=tk.BOTH, expand=True)

        insights_frame = ttk.LabelFrame(wrapper, text="Visual insights", padding=15)
        insights_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(20, 0))
        insights_frame.columnconfigure(0, weight=1)
        insights_frame.columnconfigure(1, weight=1)
        insights_frame.rowconfigure(0, weight=1)

        self.recipe_canvas = tk.Canvas(insights_frame, height=180, highlightthickness=0)
        self.recipe_canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.usage_canvas = tk.Canvas(insights_frame, height=180, highlightthickness=0)
        self.usage_canvas.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        info_bar = ttk.Frame(insights_frame)
        info_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.top_recipe_var = tk.StringVar()
        self.top_ingredient_var = tk.StringVar()
        ttk.Label(info_bar, textvariable=self.top_recipe_var).pack(side=tk.LEFT)
        ttk.Label(info_bar, textvariable=self.top_ingredient_var).pack(side=tk.RIGHT)

        low_stock_frame = ttk.LabelFrame(wrapper, text="Low stock alerts", padding=15)
        low_stock_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        self.low_stock_text = tk.Text(low_stock_frame, height=4, wrap=tk.WORD, highlightthickness=0, borderwidth=0)
        self.low_stock_text.pack(fill=tk.BOTH, expand=True)
        self.low_stock_text.configure(state=tk.DISABLED)

        action_bar = ttk.Frame(wrapper)
        action_bar.grid(row=4, column=0, columnspan=2, pady=15)
        ttk.Button(action_bar, text="Refresh reports", command=self.update_reports).pack()

        self.register_theme_observer(self.apply_theme)

    def on_show(self, **_: object) -> None:
        self.update_reports()

    def update_reports(self) -> None:
        palette = self.app.current_palette or THEME_PALETTES["Light"]

        for row in self.recipe_report.get_children():
            self.recipe_report.delete(row)
        recipe_counts = self.app.db.recipe_cook_counts()
        recipe_sorted = sorted(recipe_counts, key=lambda entry: entry[1], reverse=True)
        for name, count in recipe_sorted:
            self.recipe_report.insert("", tk.END, values=(name, count))

        for row in self.usage_report.get_children():
            self.usage_report.delete(row)
        usage_rows: List[tuple[str, float, str]] = []
        for name, used_base, unit, conversion in self.app.db.ingredient_usage_totals():
            used_display = used_base / conversion if conversion else 0.0
            usage_rows.append((name, used_display, unit))
        usage_sorted = sorted(usage_rows, key=lambda entry: entry[1], reverse=True)
        for name, used_display, unit in usage_sorted:
            self.usage_report.insert(
                "",
                tk.END,
                values=(name, f"{used_display:.2f}", unit),
            )

        recipe_chart = [(name, float(count)) for name, count in recipe_sorted if count > 0]
        usage_chart = [(name, amount) for name, amount, _ in usage_sorted if amount > 0]
        self.draw_bar_chart(
            self.recipe_canvas,
            palette,
            recipe_chart,
            value_formatter=lambda value: f"{int(value)} cooks",
        )
        self.draw_bar_chart(
            self.usage_canvas,
            palette,
            usage_chart,
            value_formatter=lambda value: f"{value:.1f}",
        )

        if recipe_sorted and recipe_sorted[0][1] > 0:
            self.top_recipe_var.set(f"Most cooked: {recipe_sorted[0][0]} ({recipe_sorted[0][1]} times)")
        else:
            self.top_recipe_var.set("Cook a recipe to see popularity trends.")

        if usage_sorted and usage_sorted[0][1] > 0:
            top_name, amount, unit = usage_sorted[0]
            self.top_ingredient_var.set(f"Heaviest use: {top_name} ({amount:.1f} {unit})")
        else:
            self.top_ingredient_var.set("Ingredient usage data will appear after cooking sessions.")

        low_items = self.app.db.low_stock_items()
        self.low_stock_text.configure(state=tk.NORMAL)
        self.low_stock_text.delete("1.0", tk.END)
        if low_items:
            for item in low_items:
                self.low_stock_text.insert(
                    tk.END,
                    f"⚠ {item.name} is low (remaining {item.quantity_display} {item.display_unit})\n",
                )
        else:
            self.low_stock_text.insert(tk.END, "All inventory items meet their thresholds.\n")
        self.low_stock_text.configure(state=tk.DISABLED)

    def draw_bar_chart(
        self,
        canvas: tk.Canvas,
        palette: Dict[str, str],
        data: List[tuple[str, float]],
        *,
        value_formatter: Callable[[float], str],
    ) -> None:
        canvas.configure(bg=palette["surface"], highlightbackground=palette["border"], highlightcolor=palette["border"])
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(int(canvas.winfo_width()), 300)
        height = max(int(canvas.winfo_height()), 160)
        canvas.configure(width=width, height=height)

        if not data:
            canvas.create_text(
                width / 2,
                height / 2,
                text="No data to display yet",
                fill=palette["muted"],
                font=get_font(12, "normal", "italic"),
            )
            return

        max_value = max(value for _, value in data)
        if max_value <= 0:
            canvas.create_text(
                width / 2,
                height / 2,
                text="Run more sessions to build insights",
                fill=palette["muted"],
                font=get_font(12, "normal", "italic"),
            )
            return

        top_n = data[:5]
        bar_height = 26
        padding = 18
        spacing = 12
        for idx, (label, value) in enumerate(top_n):
            y0 = padding + idx * (bar_height + spacing)
            y1 = y0 + bar_height
            available_width = width - 160
            x1 = padding + (value / max_value) * max(available_width, 50)
            canvas.create_rectangle(padding, y0, x1, y1, fill=palette["accent"], width=0)
            canvas.create_text(padding + 4, (y0 + y1) / 2, text=label, anchor="w", fill=palette["text"])
            canvas.create_text(
                width - padding,
                (y0 + y1) / 2,
                text=value_formatter(value),
                anchor="e",
                fill=palette["text"],
            )

    def apply_theme(self, palette: Dict[str, str]) -> None:
        self.low_stock_text.configure(
            bg=palette["surface"],
            fg=palette["text"],
            insertbackground=palette["text"],
            highlightbackground=palette["border"],
            highlightcolor=palette["border"],
        )
        for canvas in (self.recipe_canvas, self.usage_canvas):
            canvas.configure(bg=palette["surface"], highlightbackground=palette["border"], highlightcolor=palette["border"])
        self.top_recipe_var.set(self.top_recipe_var.get())
        self.top_ingredient_var.set(self.top_ingredient_var.get())


def main() -> None:
    app = KitchenManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
