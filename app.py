"""Tkinter based Kitchen Manager application.

The interface guides the user through the workflows captured in the success
criteria: secure authentication, inventory oversight, recipe management,
cooking checklists and data driven reports.  The GUI intentionally stays
within the desktop Python ecosystem (Tkinter + SQLite) so that no HTML or
external runtime is required.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from database import DatabaseManager


class KitchenManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Kitchen Manager")
        self.geometry("1000x720")
        self.minsize(860, 640)
        self.db = DatabaseManager()
        self.current_user: str | None = None

        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.frames: dict[type[BaseFrame], BaseFrame] = {}
        for frame_cls in (
            LoginFrame,
            RegisterFrame,
            DashboardFrame,
            InventoryFrame,
            RecipeFrame,
            ReportsFrame,
        ):
            frame = frame_cls(parent=container, app=self)
            self.frames[frame_cls] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginFrame)

    def show_frame(self, frame_cls: type["BaseFrame"], **kwargs) -> None:
        frame = self.frames[frame_cls]
        frame.tkraise()
        frame.on_show(**kwargs)

    def on_login(self, username: str) -> None:
        self.current_user = username
        messagebox.showinfo("Login Successful", f"Welcome back {username}!")
        dashboard: DashboardFrame = self.frames[DashboardFrame]  # type: ignore[assignment]
        dashboard.set_username(username)
        self.show_frame(DashboardFrame)

    def logout(self) -> None:
        self.current_user = None
        self.show_frame(LoginFrame)


class BaseFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, padding=30)
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def on_show(self, **_: object) -> None:  # pragma: no cover - overridden in children
        pass


class LoginFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)
        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)

        title = ttk.Label(wrapper, text="Kitchen Manager Login", font=("Segoe UI", 22, "bold"))
        title.grid(row=0, column=0, pady=(0, 20))

        form = ttk.Frame(wrapper)
        form.grid(row=1, column=0, sticky="nsew")
        for i in range(2):
            form.rowconfigure(i, weight=1)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.username_entry = ttk.Entry(form)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.password_entry = ttk.Entry(form, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        button_bar = ttk.Frame(wrapper)
        button_bar.grid(row=2, column=0, pady=(20, 0))
        login_btn = ttk.Button(button_bar, text="Login", command=self.handle_login)
        register_btn = ttk.Button(button_bar, text="Register", command=self.open_register)
        login_btn.grid(row=0, column=0, padx=5)
        register_btn.grid(row=0, column=1, padx=5)

    def handle_login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Missing information", "Please enter username and password.")
            return
        if self.app.db.authenticate_user(username, password):
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.app.on_login(username)
        else:
            messagebox.showerror("Login failed", "Incorrect username or password.")

    def open_register(self) -> None:
        self.app.show_frame(RegisterFrame)

    def on_show(self, **_: object) -> None:
        self.username_entry.focus_set()


class RegisterFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)
        wrapper = ttk.Frame(self)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)

        ttk.Label(wrapper, text="Create an account", font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, pady=(0, 20)
        )

        form = ttk.Frame(wrapper)
        form.grid(row=1, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.username_entry = ttk.Entry(form)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.password_entry = ttk.Entry(form, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Confirm Password:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.confirm_entry = ttk.Entry(form, show="*")
        self.confirm_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        button_bar = ttk.Frame(wrapper)
        button_bar.grid(row=2, column=0, pady=(20, 0))
        register_btn = ttk.Button(button_bar, text="Register", command=self.handle_register)
        back_btn = ttk.Button(button_bar, text="Back to login", command=self.go_back)
        register_btn.grid(row=0, column=0, padx=5)
        back_btn.grid(row=0, column=1, padx=5)

    def handle_register(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        if not username or not password:
            messagebox.showerror("Missing information", "Username and password are required.")
            return
        if password != confirm:
            messagebox.showerror("Mismatch", "Password confirmation does not match.")
            return
        try:
            self.app.db.register_user(username, password)
        except Exception as exc:  # sqlite3.IntegrityError etc.
            messagebox.showerror("Unable to register", str(exc))
            return
        messagebox.showinfo("Success", "Account created. Please login.")
        self.go_back()

    def go_back(self) -> None:
        self.app.show_frame(LoginFrame)

    def on_show(self, **_: object) -> None:
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.confirm_entry.delete(0, tk.END)
        self.username_entry.focus_set()


class DashboardFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.welcome_message = ttk.Label(self, text="Welcome back!", font=("Segoe UI", 18, "bold"))
        self.welcome_message.grid(row=0, column=0, sticky="w")

        greeting = ttk.Label(self, text="Welcome to kitchen manager", font=("Segoe UI", 24))
        greeting.grid(row=1, column=0, sticky="n", pady=20)

        buttons = ttk.Frame(self)
        buttons.grid(row=2, column=0, pady=30)

        inventory_btn = ttk.Button(
            buttons,
            text="📦 Inventory",
            command=lambda: self.app.show_frame(InventoryFrame),
            width=20,
        )
        recipes_btn = ttk.Button(
            buttons,
            text="🍲 Recipes",
            command=lambda: self.app.show_frame(RecipeFrame),
            width=20,
        )
        reports_btn = ttk.Button(
            buttons,
            text="📊 Reports",
            command=lambda: self.app.show_frame(ReportsFrame),
            width=20,
        )
        logout_btn = ttk.Button(buttons, text="🚪 Logout", command=self.app.logout, width=20)

        inventory_btn.grid(row=0, column=0, padx=10, pady=10)
        recipes_btn.grid(row=0, column=1, padx=10, pady=10)
        reports_btn.grid(row=1, column=0, padx=10, pady=10)
        logout_btn.grid(row=1, column=1, padx=10, pady=10)

    def set_username(self, username: str) -> None:
        self.welcome_message.config(text=f"Welcome back {username}")

    def on_show(self, **_: object) -> None:
        pass


class InventoryFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)
        self.notifications_var = tk.StringVar()

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Inventory", font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(header, text="⬅ Back", command=lambda: self.app.show_frame(DashboardFrame)).grid(
            row=0, column=1, sticky="e"
        )

        notification_label = ttk.Label(
            self,
            textvariable=self.notifications_var,
            foreground="#c0392b",
            font=("Segoe UI", 12, "bold"),
        )
        notification_label.grid(row=1, column=0, sticky="ew", pady=(5, 10))

        self.tree = ttk.Treeview(
            self,
            columns=("Quantity", "Unit", "Minimum", "Status"),
            show="headings",
            height=12,
        )
        self.tree.heading("Quantity", text="Quantity")
        self.tree.heading("Unit", text="Unit")
        self.tree.heading("Minimum", text="Minimum")
        self.tree.heading("Status", text="Status")
        self.tree.column("Quantity", anchor="center")
        self.tree.column("Unit", anchor="center")
        self.tree.column("Minimum", anchor="center")
        self.tree.column("Status", anchor="center")
        self.tree.grid(row=2, column=0, sticky="nsew")

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky="ns")

        button_bar = ttk.Frame(self)
        button_bar.grid(row=3, column=0, pady=15)

        ttk.Button(button_bar, text="Add item", command=self.add_item).grid(row=0, column=0, padx=5)
        ttk.Button(button_bar, text="Update quantity", command=self.update_quantity).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(button_bar, text="Delete item", command=self.delete_item).grid(
            row=0, column=2, padx=5
        )

    def on_show(self, **_: object) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        items = self.app.db.fetch_inventory_items()
        low_stock_messages = []
        for item in items:
            status = "✅ OK"
            if item.quantity <= item.min_quantity:
                status = f"⚠️ Low stock"
                low_stock_messages.append(f"Low Stock: {item.name}")
            min_display, min_unit = self.app.db.format_quantity(item.min_quantity, item.base_unit)
            self.tree.insert(
                "",
                tk.END,
                iid=str(item.id),
                values=(f"{item.display_quantity:.2f}", item.display_unit, f"{min_display:.2f} {min_unit}", status),
            )
        self.notifications_var.set(" | ".join(low_stock_messages))

    def _prompt_unit(self, prompt: str) -> str | None:
        units = list(DatabaseManager.UNIT_CONVERSIONS.keys())
        unit = simpledialog.askstring("Unit", f"{prompt} ({', '.join(units)}):", parent=self)
        if unit is None:
            return None
        unit = unit.lower().strip()
        if unit not in units:
            raise ValueError("Unsupported unit")
        return unit

    def add_item(self) -> None:
        name = simpledialog.askstring("Item name", "Enter inventory item name:", parent=self)
        if not name:
            return
        try:
            quantity_text = simpledialog.askstring("Quantity", "Enter starting quantity:", parent=self)
            if quantity_text is None:
                return
            quantity = float(quantity_text)
            unit = self._prompt_unit("Select unit")
            if unit is None:
                return
            minimum_text = simpledialog.askstring(
                "Minimum quantity", "Enter minimum quantity threshold:", parent=self
            )
            if minimum_text is None:
                return
            minimum = float(minimum_text)
            self.app.db.add_inventory_item(name.strip(), quantity, unit, minimum)
            self.refresh_items()
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def update_quantity(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Select item", "Please choose an item to update.")
            return
        item_id = int(selection[0])
        try:
            quantity_text = simpledialog.askstring("Quantity", "Enter new quantity:", parent=self)
            if quantity_text is None:
                return
            quantity = float(quantity_text)
            unit = self._prompt_unit("Select unit")
            if unit is None:
                return
            self.app.db.update_inventory_quantity(item_id, quantity, unit)
            self.refresh_items()
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def delete_item(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Select item", "Please choose an item to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected inventory item?"):
            return
        item_id = int(selection[0])
        self.app.db.delete_inventory_item(item_id)
        self.refresh_items()


class RecipeFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)
        self.selected_recipe_id: int | None = None

        header = ttk.Frame(self)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Recipes", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="⬅ Back", command=lambda: self.app.show_frame(DashboardFrame)).grid(
            row=0, column=1, sticky="e"
        )

        self.recipe_tree = ttk.Treeview(self, columns=("Description",), show="headings", height=12)
        self.recipe_tree.heading("Description", text="Description")
        self.recipe_tree.column("Description", width=260)
        self.recipe_tree.grid(row=1, column=0, sticky="nsew")
        self.recipe_tree.bind("<<TreeviewSelect>>", lambda _: self.update_details())

        recipe_scroll = ttk.Scrollbar(self, orient="vertical", command=self.recipe_tree.yview)
        self.recipe_tree.configure(yscrollcommand=recipe_scroll.set)
        recipe_scroll.grid(row=1, column=1, sticky="ns")

        details = ttk.Frame(self, padding=(20, 0))
        details.grid(row=1, column=2, sticky="nsew")
        details.columnconfigure(0, weight=1)

        ttk.Label(details, text="Ingredients", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.ingredients_list = tk.Listbox(details, height=8)
        self.ingredients_list.grid(row=1, column=0, sticky="nsew", pady=5)

        ttk.Label(details, text="Checklist", font=("Segoe UI", 14, "bold")).grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        self.steps_list = tk.Listbox(details, height=8)
        self.steps_list.grid(row=3, column=0, sticky="nsew", pady=5)

        details.rowconfigure(1, weight=1)
        details.rowconfigure(3, weight=1)

        button_bar = ttk.Frame(self)
        button_bar.grid(row=2, column=0, columnspan=3, pady=15)

        ttk.Button(button_bar, text="Add recipe", command=self.add_recipe).grid(row=0, column=0, padx=5)
        ttk.Button(button_bar, text="Manage ingredients", command=self.manage_ingredients).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(button_bar, text="Start cooking", command=self.start_cooking).grid(
            row=0, column=2, padx=5
        )
        ttk.Button(button_bar, text="Delete recipe", command=self.delete_recipe).grid(
            row=0, column=3, padx=5
        )

        self.columnconfigure(0, weight=3)
        self.columnconfigure(2, weight=2)
        self.rowconfigure(1, weight=1)

    def on_show(self, **_: object) -> None:
        self.refresh_recipes()

    def refresh_recipes(self) -> None:
        for item in self.recipe_tree.get_children():
            self.recipe_tree.delete(item)
        for recipe in self.app.db.fetch_recipes():
            description = recipe["description"] or ""
            self.recipe_tree.insert("", tk.END, iid=str(recipe["id"]), values=(description,))
        self.ingredients_list.delete(0, tk.END)
        self.steps_list.delete(0, tk.END)
        self.selected_recipe_id = None

    def add_recipe(self) -> None:
        dialog = RecipeDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            name, description, steps = dialog.result
            try:
                recipe_id = self.app.db.add_recipe(name, description, steps)
                messagebox.showinfo("Recipe created", "Add ingredients to complete the recipe setup.")
                self.refresh_recipes()
                self.recipe_tree.selection_set(str(recipe_id))
                self.manage_ingredients()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    def manage_ingredients(self) -> None:
        selection = self.recipe_tree.selection()
        if not selection:
            messagebox.showerror("Select recipe", "Choose a recipe to manage ingredients.")
            return
        recipe_id = int(selection[0])
        dialog = IngredientDialog(self, recipe_id)
        self.wait_window(dialog)
        self.update_details()

    def update_details(self) -> None:
        selection = self.recipe_tree.selection()
        if not selection:
            return
        recipe_id = int(selection[0])
        self.selected_recipe_id = recipe_id
        self.ingredients_list.delete(0, tk.END)
        for _item_id, name, quantity, base_unit in self.app.db.fetch_recipe_ingredients(recipe_id):
            display_qty, display_unit = self.app.db.format_quantity(quantity, base_unit)
            self.ingredients_list.insert(tk.END, f"{name} - {display_qty:.2f} {display_unit}")

        self.steps_list.delete(0, tk.END)
        for step in self.app.db.fetch_recipe_steps(recipe_id):
            self.steps_list.insert(tk.END, step)

    def start_cooking(self) -> None:
        if self.selected_recipe_id is None:
            messagebox.showerror("Select recipe", "Choose a recipe to start cooking.")
            return
        sufficient, shortages = self.app.db.has_sufficient_inventory(self.selected_recipe_id)
        if not sufficient:
            shortage_text = "\n".join(shortages)
            messagebox.showerror("Insufficient stock", f"Cannot start cooking:\n{shortage_text}")
            return
        try:
            self.app.db.consume_recipe(self.selected_recipe_id)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        steps = self.app.db.fetch_recipe_steps(self.selected_recipe_id)
        ChecklistWindow(self, steps)
        messagebox.showinfo("Inventory updated", "Ingredients deducted from inventory.")
        inventory_frame = self.app.frames.get(InventoryFrame)
        if isinstance(inventory_frame, InventoryFrame):
            inventory_frame.refresh_items()

    def delete_recipe(self) -> None:
        selection = self.recipe_tree.selection()
        if not selection:
            messagebox.showerror("Select recipe", "Choose a recipe to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected recipe?"):
            return
        recipe_id = int(selection[0])
        self.app.db.delete_recipe(recipe_id)
        self.refresh_recipes()


class RecipeDialog(tk.Toplevel):
    def __init__(self, parent: RecipeFrame) -> None:
        super().__init__(parent)
        self.title("Add recipe")
        self.geometry("420x420")
        self.result: tuple[str, str, list[str]] | None = None
        self.transient(parent)
        self.grab_set()

        ttk.Label(self, text="Recipe name:").pack(anchor="w", padx=10, pady=5)
        self.name_entry = ttk.Entry(self)
        self.name_entry.pack(fill="x", padx=10)

        ttk.Label(self, text="Description:").pack(anchor="w", padx=10, pady=5)
        self.description_entry = ttk.Entry(self)
        self.description_entry.pack(fill="x", padx=10)

        ttk.Label(self, text="Steps (one per line):").pack(anchor="w", padx=10, pady=5)
        self.steps_text = tk.Text(self, height=10)
        self.steps_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        button_bar = ttk.Frame(self)
        button_bar.pack(pady=10)
        ttk.Button(button_bar, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=5)
        ttk.Button(button_bar, text="Save", command=self.save).grid(row=0, column=1, padx=5)

        self.name_entry.focus_set()

    def save(self) -> None:
        name = self.name_entry.get().strip()
        description = self.description_entry.get().strip()
        steps = [line.strip() for line in self.steps_text.get("1.0", tk.END).splitlines() if line.strip()]
        if not name or not steps:
            messagebox.showerror("Missing data", "Recipe name and at least one step are required.")
            return
        self.result = (name, description, steps)
        self.destroy()


class IngredientDialog(tk.Toplevel):
    def __init__(self, parent: RecipeFrame, recipe_id: int) -> None:
        super().__init__(parent)
        self.title("Manage ingredients")
        self.geometry("380x360")
        self.recipe_id = recipe_id
        self.parent_frame = parent
        self.transient(parent)
        self.grab_set()

        ttk.Label(self, text="Select inventory item:").pack(anchor="w", padx=10, pady=5)
        self.item_var = tk.StringVar()
        items = parent.app.db.fetch_inventory_items()
        self.item_options = {item.name: item for item in items}
        self.item_combo = ttk.Combobox(
            self,
            textvariable=self.item_var,
            values=list(self.item_options.keys()),
            state="readonly",
        )
        self.item_combo.pack(fill="x", padx=10)
        self.item_combo.bind("<<ComboboxSelected>>", lambda _: self._update_unit_hint())

        ttk.Label(self, text="Quantity needed:").pack(anchor="w", padx=10, pady=5)
        self.quantity_entry = ttk.Entry(self)
        self.quantity_entry.pack(fill="x", padx=10)

        ttk.Label(self, text="Unit:").pack(anchor="w", padx=10, pady=5)
        self.unit_var = tk.StringVar(value="g")
        units = list(DatabaseManager.UNIT_CONVERSIONS.keys())
        self.unit_combo = ttk.Combobox(self, textvariable=self.unit_var, values=units, state="readonly")
        self.unit_combo.pack(fill="x", padx=10)

        self.unit_hint = ttk.Label(self, text="", foreground="#555")
        self.unit_hint.pack(anchor="w", padx=10, pady=(2, 8))
        self._update_unit_hint()

        ttk.Button(self, text="Add ingredient", command=self.add_ingredient).pack(pady=10)

        self.ingredients_box = tk.Listbox(self, height=6)
        self.ingredients_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_list()

    def refresh_list(self) -> None:
        self.ingredients_box.delete(0, tk.END)
        for _, name, quantity, base_unit in self.parent_frame.app.db.fetch_recipe_ingredients(
            self.recipe_id
        ):
            display_qty, display_unit = self.parent_frame.app.db.format_quantity(quantity, base_unit)
            self.ingredients_box.insert(tk.END, f"{name} - {display_qty:.2f} {display_unit}")

    def add_ingredient(self) -> None:
        item_name = self.item_var.get()
        if item_name not in self.item_options:
            messagebox.showerror("Invalid selection", "Choose an inventory item.")
            return
        try:
            quantity = float(self.quantity_entry.get())
            unit = self.unit_var.get()
        except ValueError:
            messagebox.showerror("Invalid quantity", "Enter a numeric quantity.")
            return
        inventory_item = self.item_options[item_name]
        try:
            base_quantity = self.parent_frame.app.db.convert_quantity(quantity, unit, inventory_item.base_unit)
            self.parent_frame.app.db.add_recipe_ingredient(
                self.recipe_id, inventory_item.id, base_quantity
            )
            self.refresh_list()
            self.parent_frame.update_details()
        except Exception as exc:
            messagebox.showerror("Unable to add ingredient", str(exc))

    def _update_unit_hint(self) -> None:
        item_name = self.item_var.get()
        if item_name in self.item_options:
            inventory_item = self.item_options[item_name]
            self.unit_hint.config(
                text=f"Inventory unit: {inventory_item.base_unit}. Quantities convert automatically."
            )
            default_unit = inventory_item.base_unit
            self.unit_var.set(default_unit if default_unit in DatabaseManager.UNIT_CONVERSIONS else "unit")
        else:
            self.unit_hint.config(text="")

class ChecklistWindow(tk.Toplevel):
    def __init__(self, parent: RecipeFrame, steps: list[str]) -> None:
        super().__init__(parent)
        self.title("Cooking checklist")
        self.geometry("360x480")
        self.transient(parent)
        self.grab_set()

        ttk.Label(self, text="Tick each step as you go", font=("Segoe UI", 14, "bold")).pack(
            pady=10
        )
        self.step_vars: list[tk.BooleanVar] = []
        for step in steps:
            var = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(self, text=step, variable=var, command=self._check_completion)
            chk.pack(anchor="w", padx=10, pady=4)
            self.step_vars.append(var)

    def _check_completion(self) -> None:
        if all(var.get() for var in self.step_vars):
            messagebox.showinfo("Recipe completed", "Recipe completed")


class ReportsFrame(BaseFrame):
    def __init__(self, parent: tk.Widget, app: KitchenManagerApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Reports", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="⬅ Back", command=lambda: self.app.show_frame(DashboardFrame)).grid(
            row=0, column=1, sticky="e"
        )

        ttk.Label(self, text="Recipe popularity", font=("Segoe UI", 14, "bold")).grid(
            row=1, column=0, sticky="w", pady=(20, 5)
        )
        self.recipe_stats = tk.Listbox(self, height=10)
        self.recipe_stats.grid(row=2, column=0, sticky="nsew", padx=(0, 20))

        ttk.Label(self, text="Ingredient usage", font=("Segoe UI", 14, "bold")).grid(
            row=1, column=1, sticky="w", pady=(20, 5)
        )
        self.ingredient_stats = tk.Listbox(self, height=10)
        self.ingredient_stats.grid(row=2, column=1, sticky="nsew")

        ttk.Label(self, text="Low stock alerts", font=("Segoe UI", 14, "bold")).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(20, 5)
        )
        self.low_stock_box = tk.Listbox(self, height=6)
        self.low_stock_box.grid(row=4, column=0, columnspan=2, sticky="nsew")

        self.rowconfigure(2, weight=1)
        self.rowconfigure(4, weight=1)

    def on_show(self, **_: object) -> None:
        self.refresh()

    def refresh(self) -> None:
        self.recipe_stats.delete(0, tk.END)
        for name, count in self.app.db.recipe_statistics():
            self.recipe_stats.insert(tk.END, f"{name}: cooked {count} time(s)")

        self.ingredient_stats.delete(0, tk.END)
        for name, total, unit in self.app.db.ingredient_usage_statistics():
            self.ingredient_stats.insert(tk.END, f"{name}: {total:.2f} {unit} used")

        self.low_stock_box.delete(0, tk.END)
        for item in self.app.db.low_stock_items():
            display_qty, display_unit = self.app.db.format_quantity(item.quantity, item.base_unit)
            self.low_stock_box.insert(tk.END, f"{item.name}: {display_qty:.2f} {display_unit} remaining")


def main() -> None:
    app = KitchenManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()

