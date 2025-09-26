"""Kitchen Manager desktop application built with Tkinter and SQLite."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

from database import DatabaseManager, RecipeStep

UNIT_DEFINITIONS: Dict[str, tuple[str, float]] = {
    "kg": ("g", 1000.0),
    "g": ("g", 1.0),
    "L": ("ml", 1000.0),
    "ml": ("ml", 1.0),
    "unit": ("unit", 1.0),
    "dozen": ("unit", 12.0),
}


def format_quantity(amount_base: float, conversion: float) -> str:
    return f"{amount_base / conversion:.2f}"


class KitchenManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Kitchen Manager")
        self.geometry("1100x760")
        self.minsize(960, 700)
        self.db = DatabaseManager()
        self.current_user: Optional[str] = None

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
            RecipeFrame,
            ReportsFrame,
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


class LoginFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)

        ttk.Label(wrapper, text="Kitchen Manager Login", font=("Segoe UI", 26, "bold")).grid(
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

        ttk.Label(wrapper, text="Create an account", font=("Segoe UI", 26, "bold")).grid(
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
        wrapper.columnconfigure((0, 1), weight=1)
        wrapper.rowconfigure(1, weight=1)

        self.greeting_var = tk.StringVar()
        greeting = ttk.Label(wrapper, textvariable=self.greeting_var, font=("Segoe UI", 24, "bold"))
        greeting.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(wrapper, text="Welcome to kitchen manager", font=("Segoe UI", 14)).grid(
            row=1, column=0, columnspan=2
        )

        card_container = ttk.Frame(wrapper)
        card_container.grid(row=2, column=0, columnspan=2, pady=40)

        cards = [
            ("Inventory", "Manage stock levels, units and thresholds", InventoryFrame),
            ("Recipes", "Curate dishes and start cooking checklists", RecipeFrame),
            ("Reports", "Analyse cooking frequency and ingredient usage", ReportsFrame),
        ]
        for idx, (title, description, frame_cls) in enumerate(cards):
            card = ttk.Frame(card_container, padding=20, relief=tk.RIDGE, borderwidth=2)
            card.grid(row=0, column=idx, padx=15)
            ttk.Label(card, text=title, font=("Segoe UI", 18, "bold")).pack(anchor="center")
            ttk.Label(card, text=description, wraplength=220, justify=tk.CENTER).pack(pady=10)
            ttk.Button(card, text=f"Open {title}", command=lambda cls=frame_cls: self.app.show_frame(cls)).pack()

        logout_bar = ttk.Frame(wrapper)
        logout_bar.grid(row=3, column=0, columnspan=2, pady=(40, 0))
        ttk.Button(logout_bar, text="Logout", command=self.app.logout).pack()

    def set_username(self, username: str) -> None:
        self.greeting_var.set(f"Welcome back {username}")


class InventoryFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Inventory", font=("Segoe UI", 22, "bold")).pack(side=tk.LEFT)
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
        ttk.Label(side_panel, textvariable=self.low_stock_var, foreground="red", wraplength=280, justify=tk.LEFT).grid(
            row=2, column=0, sticky="nw", pady=(20, 0)
        )

        self.editing_item_id: Optional[int] = None

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

    def delete_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Select an item to delete")
            return
        item_id = int(selection[0])
        if messagebox.askyesno("Confirm", "Remove the selected inventory item?"):
            self.app.db.delete_inventory_item(item_id)
            self.refresh_inventory()


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
        ttk.Label(header, text="Recipes", font=("Segoe UI", 22, "bold")).pack(side=tk.LEFT)
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
        ttk.Label(detail_panel, textvariable=self.detail_name, font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.detail_description = tk.StringVar()
        ttk.Label(detail_panel, textvariable=self.detail_description, wraplength=420, justify=tk.LEFT).grid(
            row=1, column=0, sticky="w", pady=(10, 20)
        )

        ingredients_frame = ttk.LabelFrame(detail_panel, text="Ingredients", padding=10)
        ingredients_frame.grid(row=2, column=0, sticky="nsew")
        self.ingredients_list = tk.Listbox(ingredients_frame, height=6)
        self.ingredients_list.pack(fill=tk.BOTH, expand=True)

        steps_frame = ttk.LabelFrame(detail_panel, text="Steps", padding=10)
        steps_frame.grid(row=3, column=0, sticky="nsew", pady=(20, 0))
        self.steps_list = tk.Listbox(steps_frame, height=8)
        self.steps_list.pack(fill=tk.BOTH, expand=True)

        self.selected_recipe_id: Optional[int] = None

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
        usage: List[tuple[int, float]] = []
        missing: List[str] = []
        for ingredient in ingredients:
            item = self.app.db.get_inventory_item(ingredient.inventory_item_id)
            if item is None:
                missing.append("Unknown inventory item")
                continue
            if item.quantity_base < ingredient.quantity_base:
                amount = format_quantity(ingredient.quantity_base, item.conversion_to_base)
                missing.append(f"{item.name} requires {amount} {item.display_unit}")
            else:
                usage.append((item.id, ingredient.quantity_base))
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


class RecipeDialog(tk.Toplevel):
    def __init__(self, parent: RecipeFrame, db: DatabaseManager) -> None:
        super().__init__(parent)
        self.title("Add recipe")
        self.resizable(False, False)
        self.db = db
        self.transient(parent)
        self.grab_set()

        self.columnconfigure(0, weight=1)

        ttk.Label(self, text="Recipe name:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.name_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.name_var, width=40).grid(row=1, column=0, padx=10, sticky="ew")

        ttk.Label(self, text="Description (optional):").grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))
        self.description_text = tk.Text(self, width=50, height=4)
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
        self.steps_text = tk.Text(self, width=50, height=8)
        self.steps_text.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="ew")

        button_bar = ttk.Frame(self)
        button_bar.grid(row=7, column=0, pady=10)
        ttk.Button(button_bar, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_bar, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.ingredients: List[tuple[int, float]] = []

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

        ttk.Label(self, text="Tick steps as you progress", font=("Segoe UI", 14, "bold")).pack(pady=(15, 10))
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


class ReportsFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)

        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.columnconfigure(1, weight=1)
        wrapper.rowconfigure(1, weight=1)

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Reports", font=("Segoe UI", 22, "bold")).pack(side=tk.LEFT)
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

        low_stock_frame = ttk.LabelFrame(wrapper, text="Low stock alerts", padding=15)
        low_stock_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        self.low_stock_text = tk.Text(low_stock_frame, height=4, wrap=tk.WORD)
        self.low_stock_text.pack(fill=tk.BOTH, expand=True)
        self.low_stock_text.configure(state=tk.DISABLED)

        action_bar = ttk.Frame(wrapper)
        action_bar.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(action_bar, text="Refresh reports", command=self.update_reports).pack()

    def on_show(self, **_: object) -> None:
        self.update_reports()

    def update_reports(self) -> None:
        for row in self.recipe_report.get_children():
            self.recipe_report.delete(row)
        for name, count in self.app.db.recipe_cook_counts():
            self.recipe_report.insert("", tk.END, values=(name, count))

        for row in self.usage_report.get_children():
            self.usage_report.delete(row)
        for name, used_base, unit, conversion in self.app.db.ingredient_usage_totals():
            self.usage_report.insert(
                "",
                tk.END,
                values=(name, f"{used_base / conversion:.2f}", unit),
            )

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


def main() -> None:
    app = KitchenManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
