"""SQLite data layer for the Kitchen Manager desktop application."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DB_PATH = Path("kitchen_manager.db")

UNIT_INFO: Dict[str, tuple[str, float]] = {
    "kg": ("g", 1000.0),
    "g": ("g", 1.0),
    "L": ("ml", 1000.0),
    "ml": ("ml", 1.0),
    "unit": ("unit", 1.0),
    "dozen": ("unit", 12.0),
}


@dataclass(frozen=True)
class InventoryItem:
    id: int
    name: str
    quantity_base: float
    display_unit: str
    base_unit: str
    conversion_to_base: float
    low_stock_threshold_base: float

    @property
    def quantity_display(self) -> float:
        return round(self.quantity_base / self.conversion_to_base, 3)

    @property
    def threshold_display(self) -> float:
        return round(self.low_stock_threshold_base / self.conversion_to_base, 3)

    @property
    def is_low(self) -> bool:
        return self.quantity_base <= self.low_stock_threshold_base


@dataclass(frozen=True)
class Recipe:
    id: int
    name: str
    description: str


@dataclass(frozen=True)
class RecipeIngredient:
    recipe_id: int
    inventory_item_id: int
    quantity_base: float


@dataclass(frozen=True)
class RecipeStep:
    recipe_id: int
    position: int
    instruction: str


@dataclass(frozen=True)
class Supplier:
    id: int
    name: str
    contact_person: str
    phone: str
    email: str
    notes: str


@dataclass(frozen=True)
class VendorOrder:
    id: int
    supplier_id: int
    supplier_name: str
    inventory_item_id: int
    inventory_item_name: str
    quantity_base: float
    display_unit: str
    conversion_to_base: float
    status: str
    ordered_at: str
    expected_date: Optional[str]
    received_at: Optional[str]


@dataclass(frozen=True)
class CustomerOrder:
    id: int
    customer_name: str
    recipe_id: int
    recipe_name: str
    servings: int
    status: str
    created_at: str


class DatabaseManager:
    """High level helper that encapsulates all persistence operations."""

    def __init__(self, path: Path | str = DB_PATH) -> None:
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._initialise_schema()
        self._seed_initial_data()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _initialise_schema(self) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS inventory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    quantity_base REAL NOT NULL,
                    display_unit TEXT NOT NULL,
                    base_unit TEXT NOT NULL,
                    conversion_to_base REAL NOT NULL,
                    low_stock_threshold_base REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS recipe_ingredients (
                    recipe_id INTEGER NOT NULL,
                    inventory_item_id INTEGER NOT NULL,
                    quantity_base REAL NOT NULL,
                    PRIMARY KEY (recipe_id, inventory_item_id),
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS recipe_steps (
                    recipe_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    instruction TEXT NOT NULL,
                    PRIMARY KEY (recipe_id, position),
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS cooking_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL,
                    cooked_at TEXT NOT NULL,
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS ingredient_usage (
                    session_id INTEGER NOT NULL,
                    inventory_item_id INTEGER NOT NULL,
                    quantity_base REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES cooking_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    contact_person TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    notes TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS vendor_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    inventory_item_id INTEGER NOT NULL,
                    quantity_base REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    ordered_at TEXT NOT NULL,
                    expected_date TEXT,
                    received_at TEXT,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
                    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS customer_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    recipe_id INTEGER NOT NULL,
                    servings INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            self._connection.commit()

    def _seed_initial_data(self) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            (user_count,) = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM inventory_items")
            (inventory_count,) = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM suppliers")
            (supplier_count,) = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM recipes")
            (recipe_count,) = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM vendor_orders")
            (vendor_order_count,) = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM customer_orders")
            (customer_order_count,) = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM cooking_sessions")
            (session_count,) = cursor.fetchone()

        if user_count == 0:
            self.create_user("manager", "kitchen123")

        if not self.get_setting("restaurant_name"):
            self.set_setting("restaurant_name", "Marina Breeze Kitchen")
        if not self.get_setting("notification_email"):
            self.set_setting("notification_email", "alerts@marinabreezekitchen.example")
        if not self.get_setting("default_lead_days"):
            self.set_setting("default_lead_days", "2")
        if not self.get_setting("theme"):
            self.set_setting("theme", "Light")

        if inventory_count == 0:
            inventory_samples = [
                ("Basmati Rice", "kg", 38.0, 8.0),
                ("Chicken Breast", "kg", 22.0, 5.0),
                ("Red Onions", "kg", 20.0, 4.0),
                ("Tomatoes", "kg", 18.0, 4.0),
                ("Garlic", "kg", 7.0, 1.5),
                ("Coconut Milk", "L", 28.0, 5.0),
                ("Spice Blend", "kg", 6.0, 1.5),
                ("Plain Yogurt", "L", 22.0, 4.0),
                ("Fresh Coriander", "kg", 2.0, 0.6),
                ("Eggs", "dozen", 18.0, 5.0),
                ("Cooking Oil", "L", 28.0, 6.0),
            ]
            for name, unit, quantity, threshold in inventory_samples:
                base_unit, conversion = UNIT_INFO[unit]
                self.add_inventory_item(
                    name,
                    quantity * conversion,
                    unit,
                    base_unit,
                    conversion,
                    threshold * conversion,
                )

        if supplier_count == 0:
            supplier_samples = [
                (
                    "Marina Farms Cooperative",
                    "Lakshmi Devi",
                    "+91 98765 43210",
                    "orders@marinafarms.example",
                    "Seasonal vegetables and herbs harvested daily.",
                ),
                (
                    "Spice Route Distributors",
                    "Ravi Kumar",
                    "+91 91234 56780",
                    "sales@spiceroute.example",
                    "Regional spice blends with weekly delivery routes.",
                ),
                (
                    "Coastal Dairy Collective",
                    "Priya Narayanan",
                    "+91 99887 76655",
                    "support@coastaldairy.example",
                    "Yogurt, coconut milk, and other dairy staples.",
                ),
            ]
            for name, contact, phone, email, notes in supplier_samples:
                self.add_supplier(name, contact, phone, email, notes)

        items_map = {item.name: item for item in self.get_inventory_items()}

        if recipe_count == 0 and items_map:
            recipe_samples = [
                {
                    "name": "Chettinad Chicken Curry",
                    "description": "Slow-cooked chicken with roasted spices, coconut milk, and fresh coriander.",
                    "ingredients": [
                        ("Chicken Breast", 1.5),
                        ("Spice Blend", 0.18),
                        ("Coconut Milk", 1.2),
                        ("Red Onions", 0.8),
                        ("Tomatoes", 0.6),
                        ("Garlic", 0.12),
                        ("Cooking Oil", 0.6),
                        ("Fresh Coriander", 0.2),
                    ],
                    "steps": [
                        "Marinate chicken with spice blend and yogurt for 30 minutes.",
                        "Sauté onions, tomatoes, and garlic until browned.",
                        "Add chicken and cook until sealed, then pour in coconut milk.",
                        "Simmer until chicken is tender and garnish with coriander.",
                    ],
                },
                {
                    "name": "Chicken Biryani",
                    "description": "Layered basmati rice with marinated chicken, caramelised onions, and spices.",
                    "ingredients": [
                        ("Basmati Rice", 3.5),
                        ("Chicken Breast", 2.0),
                        ("Spice Blend", 0.25),
                        ("Plain Yogurt", 1.0),
                        ("Red Onions", 1.2),
                        ("Garlic", 0.15),
                        ("Tomatoes", 0.9),
                        ("Cooking Oil", 1.2),
                        ("Fresh Coriander", 0.15),
                    ],
                    "steps": [
                        "Par-boil basmati rice with whole spices and set aside.",
                        "Brown onions in oil, then add marinated chicken and tomatoes.",
                        "Layer rice over chicken, drizzle with yogurt, and cook on dum.",
                        "Finish with fried onions and fresh coriander before serving.",
                    ],
                },
                {
                    "name": "Tomato Egg Curry",
                    "description": "Comforting tomato gravy simmered with boiled eggs and house spice mix.",
                    "ingredients": [
                        ("Eggs", 1.5),
                        ("Tomatoes", 1.5),
                        ("Red Onions", 0.7),
                        ("Garlic", 0.1),
                        ("Coconut Milk", 0.7),
                        ("Spice Blend", 0.12),
                        ("Cooking Oil", 0.4),
                        ("Fresh Coriander", 0.1),
                    ],
                    "steps": [
                        "Boil eggs, peel, and score lightly to absorb gravy.",
                        "Cook onions, tomatoes, and garlic until silky.",
                        "Stir in spice blend and coconut milk, then add eggs.",
                        "Simmer for five minutes and finish with coriander.",
                    ],
                },
            ]
            for recipe in recipe_samples:
                ingredients: List[tuple[int, float]] = []
                for ingredient_name, amount in recipe["ingredients"]:
                    item = items_map.get(ingredient_name)
                    if item is None:
                        continue
                    ingredients.append((item.id, amount * item.conversion_to_base))
                if not ingredients:
                    continue
                self.add_recipe(recipe["name"], recipe["description"], ingredients, recipe["steps"])

        suppliers_map = {supplier.name: supplier.id for supplier in self.get_suppliers()}
        recipes_map = {recipe.name: recipe.id for recipe in self.get_recipes()}

        if vendor_order_count == 0 and suppliers_map and items_map:
            today = datetime.utcnow().date()
            vendor_samples = [
                ("Spice Route Distributors", "Spice Blend", 2.0, "In Transit", (today + timedelta(days=2)).isoformat()),
                ("Marina Farms Cooperative", "Fresh Coriander", 3.0, "Pending", (today + timedelta(days=1)).isoformat()),
                ("Coastal Dairy Collective", "Coconut Milk", 5.0, "Confirmed", (today + timedelta(days=3)).isoformat()),
            ]
            for supplier_name, item_name, quantity, status, expected in vendor_samples:
                supplier_id = suppliers_map.get(supplier_name)
                item = items_map.get(item_name)
                if supplier_id is None or item is None:
                    continue
                self.add_vendor_order(
                    supplier_id,
                    item.id,
                    quantity * item.conversion_to_base,
                    status=status,
                    expected_date=expected,
                )

        if customer_order_count == 0 and recipes_map:
            customer_samples = [
                ("Walk-in Table 5", "Chicken Biryani", 2, "Completed"),
                ("Delivery App - Senthil", "Chettinad Chicken Curry", 3, "In Progress"),
                ("Corporate Lunch", "Tomato Egg Curry", 4, "Pending"),
            ]
            for customer, recipe_name, servings, status in customer_samples:
                recipe_id = recipes_map.get(recipe_name)
                if recipe_id is None:
                    continue
                self.add_customer_order(customer, recipe_id, servings, status=status)

        if session_count == 0 and recipes_map:
            cook_plan = {
                "Chettinad Chicken Curry": 5,
                "Chicken Biryani": 4,
                "Tomato Egg Curry": 3,
            }
            for recipe_name, runs in cook_plan.items():
                recipe_id = recipes_map.get(recipe_name)
                if recipe_id is None:
                    continue
                ingredients = [
                    (ingredient.inventory_item_id, ingredient.quantity_base)
                    for ingredient in self.get_recipe_ingredients(recipe_id)
                ]
                if not ingredients:
                    continue
                for _ in range(runs):
                    self.record_cooking_session(recipe_id, ingredients)
                    for inventory_id, qty in ingredients:
                        self.adjust_inventory(inventory_id, -qty)

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------
    def create_user(self, username: str, password: str) -> bool:
        try:
            with closing(self._connection.cursor()) as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password),
                )
            self._connection.commit()
        except sqlite3.IntegrityError:
            return False
        return True

    def authenticate_user(self, username: str, password: str) -> bool:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "SELECT 1 FROM users WHERE username = ? AND password = ?",
                (username, password),
            )
            return cursor.fetchone() is not None

    # ------------------------------------------------------------------
    # Inventory helpers
    # ------------------------------------------------------------------
    def add_inventory_item(
        self,
        name: str,
        quantity_base: float,
        display_unit: str,
        base_unit: str,
        conversion_to_base: float,
        low_stock_threshold_base: float,
    ) -> int:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO inventory_items
                    (name, quantity_base, display_unit, base_unit, conversion_to_base, low_stock_threshold_base)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, quantity_base, display_unit, base_unit, conversion_to_base, low_stock_threshold_base),
            )
            new_id = int(cursor.lastrowid)
        self._connection.commit()
        return new_id

    def update_inventory_item(
        self,
        item_id: int,
        *,
        name: Optional[str] = None,
        quantity_base: Optional[float] = None,
        display_unit: Optional[str] = None,
        base_unit: Optional[str] = None,
        conversion_to_base: Optional[float] = None,
        low_stock_threshold_base: Optional[float] = None,
    ) -> None:
        fields: List[str] = []
        params: List[float | str | int] = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if quantity_base is not None:
            fields.append("quantity_base = ?")
            params.append(quantity_base)
        if display_unit is not None:
            fields.append("display_unit = ?")
            params.append(display_unit)
        if base_unit is not None:
            fields.append("base_unit = ?")
            params.append(base_unit)
        if conversion_to_base is not None:
            fields.append("conversion_to_base = ?")
            params.append(conversion_to_base)
        if low_stock_threshold_base is not None:
            fields.append("low_stock_threshold_base = ?")
            params.append(low_stock_threshold_base)
        if fields:
            params.append(item_id)
            with closing(self._connection.cursor()) as cursor:
                cursor.execute(
                    f"UPDATE inventory_items SET {', '.join(fields)} WHERE id = ?",
                    params,
                )
            self._connection.commit()

    def delete_inventory_item(self, item_id: int) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("DELETE FROM inventory_items WHERE id = ?", (item_id,))
        self._connection.commit()

    def adjust_inventory(self, item_id: int, delta_base: float) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "UPDATE inventory_items SET quantity_base = quantity_base + ? WHERE id = ?",
                (delta_base, item_id),
            )
        self._connection.commit()

    def get_inventory_items(self) -> List[InventoryItem]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT id, name, quantity_base, display_unit, base_unit, conversion_to_base, low_stock_threshold_base
                FROM inventory_items
                ORDER BY name COLLATE NOCASE
                """
            )
            rows = cursor.fetchall()
        return [
            InventoryItem(
                id=row["id"],
                name=row["name"],
                quantity_base=row["quantity_base"],
                display_unit=row["display_unit"],
                base_unit=row["base_unit"],
                conversion_to_base=row["conversion_to_base"],
                low_stock_threshold_base=row["low_stock_threshold_base"],
            )
            for row in rows
        ]

    def get_inventory_item(self, item_id: int) -> Optional[InventoryItem]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT id, name, quantity_base, display_unit, base_unit, conversion_to_base, low_stock_threshold_base
                FROM inventory_items WHERE id = ?
                """,
                (item_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return InventoryItem(
            id=row["id"],
            name=row["name"],
            quantity_base=row["quantity_base"],
            display_unit=row["display_unit"],
            base_unit=row["base_unit"],
            conversion_to_base=row["conversion_to_base"],
            low_stock_threshold_base=row["low_stock_threshold_base"],
        )

    def count_low_stock_items(self) -> int:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM inventory_items WHERE quantity_base <= low_stock_threshold_base"
            )
            (count,) = cursor.fetchone()
        return int(count)

    # ------------------------------------------------------------------
    # Supplier helpers
    # ------------------------------------------------------------------
    def add_supplier(
        self,
        name: str,
        contact_person: str = "",
        phone: str = "",
        email: str = "",
        notes: str = "",
    ) -> int:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO suppliers (name, contact_person, phone, email, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, contact_person, phone, email, notes),
            )
            new_id = int(cursor.lastrowid)
        self._connection.commit()
        return new_id

    def update_supplier(
        self,
        supplier_id: int,
        *,
        name: Optional[str] = None,
        contact_person: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        fields: List[str] = []
        params: List[str] = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if contact_person is not None:
            fields.append("contact_person = ?")
            params.append(contact_person)
        if phone is not None:
            fields.append("phone = ?")
            params.append(phone)
        if email is not None:
            fields.append("email = ?")
            params.append(email)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
        if not fields:
            return
        params.append(supplier_id)
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                f"UPDATE suppliers SET {', '.join(fields)} WHERE id = ?",
                params,
            )
        self._connection.commit()

    def delete_supplier(self, supplier_id: int) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
        self._connection.commit()

    def get_suppliers(self) -> List[Supplier]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT id, name, contact_person, phone, email, notes
                FROM suppliers
                ORDER BY name COLLATE NOCASE
                """
            )
            rows = cursor.fetchall()
        return [
            Supplier(
                id=row["id"],
                name=row["name"],
                contact_person=row["contact_person"],
                phone=row["phone"],
                email=row["email"],
                notes=row["notes"],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Vendor order helpers
    # ------------------------------------------------------------------
    def add_vendor_order(
        self,
        supplier_id: int,
        inventory_item_id: int,
        quantity_base: float,
        status: str = "Pending",
        expected_date: Optional[str] = None,
    ) -> int:
        ordered_at = datetime.utcnow().isoformat()
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO vendor_orders (
                    supplier_id, inventory_item_id, quantity_base, status, ordered_at, expected_date
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (supplier_id, inventory_item_id, quantity_base, status, ordered_at, expected_date),
            )
            order_id = int(cursor.lastrowid)
        self._connection.commit()
        return order_id

    def get_vendor_orders(self) -> List[VendorOrder]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT vo.id,
                       vo.supplier_id,
                       s.name AS supplier_name,
                       vo.inventory_item_id,
                       i.name AS inventory_item_name,
                       vo.quantity_base,
                       i.display_unit,
                       i.conversion_to_base,
                       vo.status,
                       vo.ordered_at,
                       vo.expected_date,
                       vo.received_at
                FROM vendor_orders vo
                JOIN suppliers s ON s.id = vo.supplier_id
                JOIN inventory_items i ON i.id = vo.inventory_item_id
                ORDER BY vo.ordered_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            VendorOrder(
                id=row["id"],
                supplier_id=row["supplier_id"],
                supplier_name=row["supplier_name"],
                inventory_item_id=row["inventory_item_id"],
                inventory_item_name=row["inventory_item_name"],
                quantity_base=row["quantity_base"],
                display_unit=row["display_unit"],
                conversion_to_base=row["conversion_to_base"],
                status=row["status"],
                ordered_at=row["ordered_at"],
                expected_date=row["expected_date"],
                received_at=row["received_at"],
            )
            for row in rows
        ]

    def update_vendor_order_status(self, order_id: int, status: str) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "UPDATE vendor_orders SET status = ? WHERE id = ?",
                (status, order_id),
            )
        self._connection.commit()

    def receive_vendor_order(self, order_id: int) -> None:
        received_at = datetime.utcnow().isoformat()
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT inventory_item_id, quantity_base, status, received_at
                FROM vendor_orders WHERE id = ?
                """,
                (order_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return
            if row["status"] == "Received" and row["received_at"]:
                return
            cursor.execute(
                "UPDATE vendor_orders SET status = 'Received', received_at = ? WHERE id = ?",
                (received_at, order_id),
            )
        self._connection.commit()
        self.adjust_inventory(row["inventory_item_id"], row["quantity_base"])

    def delete_vendor_order(self, order_id: int) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("DELETE FROM vendor_orders WHERE id = ?", (order_id,))
        self._connection.commit()

    def count_pending_vendor_orders(self) -> int:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM vendor_orders WHERE status != 'Received'"
            )
            (count,) = cursor.fetchone()
        return int(count)

    # ------------------------------------------------------------------
    # Customer order helpers
    # ------------------------------------------------------------------
    def add_customer_order(
        self,
        customer_name: str,
        recipe_id: int,
        servings: int,
        status: str = "Pending",
    ) -> int:
        created_at = datetime.utcnow().isoformat()
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                INSERT INTO customer_orders (customer_name, recipe_id, servings, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (customer_name, recipe_id, servings, status, created_at),
            )
            order_id = int(cursor.lastrowid)
        self._connection.commit()
        return order_id

    def get_customer_orders(self) -> List[CustomerOrder]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT co.id,
                       co.customer_name,
                       co.recipe_id,
                       r.name AS recipe_name,
                       co.servings,
                       co.status,
                       co.created_at
                FROM customer_orders co
                JOIN recipes r ON r.id = co.recipe_id
                ORDER BY co.created_at DESC
                """
            )
            rows = cursor.fetchall()
        return [
            CustomerOrder(
                id=row["id"],
                customer_name=row["customer_name"],
                recipe_id=row["recipe_id"],
                recipe_name=row["recipe_name"],
                servings=row["servings"],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def update_customer_order_status(self, order_id: int, status: str) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "UPDATE customer_orders SET status = ? WHERE id = ?",
                (status, order_id),
            )
        self._connection.commit()

    def delete_customer_order(self, order_id: int) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("DELETE FROM customer_orders WHERE id = ?", (order_id,))
        self._connection.commit()

    def count_pending_customer_orders(self) -> int:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM customer_orders WHERE status NOT IN ('Completed', 'Cancelled')"
            )
            (count,) = cursor.fetchone()
        return int(count)

    # ------------------------------------------------------------------
    # Recipe helpers
    # ------------------------------------------------------------------
    def add_recipe(
        self,
        name: str,
        description: str,
        ingredients: Iterable[tuple[int, float]],
        steps: Iterable[str],
    ) -> int:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "INSERT INTO recipes (name, description) VALUES (?, ?)",
                (name, description),
            )
            recipe_id = int(cursor.lastrowid)
            cursor.executemany(
                "INSERT INTO recipe_ingredients (recipe_id, inventory_item_id, quantity_base) VALUES (?, ?, ?)",
                ((recipe_id, inv_id, qty) for inv_id, qty in ingredients),
            )
            cursor.executemany(
                "INSERT INTO recipe_steps (recipe_id, position, instruction) VALUES (?, ?, ?)",
                ((recipe_id, idx, step.strip()) for idx, step in enumerate(steps, start=1) if step.strip()),
            )
        self._connection.commit()
        return recipe_id

    def get_recipes(self) -> List[Recipe]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("SELECT id, name, description FROM recipes ORDER BY name COLLATE NOCASE")
            rows = cursor.fetchall()
        return [Recipe(id=row["id"], name=row["name"], description=row["description"]) for row in rows]

    def get_recipe_ingredients(self, recipe_id: int) -> List[RecipeIngredient]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT recipe_id, inventory_item_id, quantity_base
                FROM recipe_ingredients WHERE recipe_id = ?
                ORDER BY inventory_item_id
                """,
                (recipe_id,),
            )
            rows = cursor.fetchall()
        return [
            RecipeIngredient(
                recipe_id=row["recipe_id"],
                inventory_item_id=row["inventory_item_id"],
                quantity_base=row["quantity_base"],
            )
            for row in rows
        ]

    def get_recipe_steps(self, recipe_id: int) -> List[RecipeStep]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT recipe_id, position, instruction
                FROM recipe_steps WHERE recipe_id = ?
                ORDER BY position
                """,
                (recipe_id,),
            )
            rows = cursor.fetchall()
        return [
            RecipeStep(
                recipe_id=row["recipe_id"],
                position=row["position"],
                instruction=row["instruction"],
            )
            for row in rows
        ]

    def delete_recipe(self, recipe_id: int) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        self._connection.commit()

    # ------------------------------------------------------------------
    # Cooking logs and analytics
    # ------------------------------------------------------------------
    def record_cooking_session(self, recipe_id: int, usage: Iterable[tuple[int, float]]) -> None:
        timestamp = datetime.utcnow().isoformat()
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "INSERT INTO cooking_sessions (recipe_id, cooked_at) VALUES (?, ?)",
                (recipe_id, timestamp),
            )
            session_id = int(cursor.lastrowid)
            cursor.executemany(
                "INSERT INTO ingredient_usage (session_id, inventory_item_id, quantity_base) VALUES (?, ?, ?)",
                ((session_id, inv_id, qty) for inv_id, qty in usage),
            )
        self._connection.commit()

    def recipe_cook_counts(self) -> list[tuple[str, int]]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT r.name, COUNT(s.id) AS count
                FROM recipes r
                LEFT JOIN cooking_sessions s ON r.id = s.recipe_id
                GROUP BY r.id
                ORDER BY r.name COLLATE NOCASE
                """
            )
            return [(row["name"], row["count"]) for row in cursor.fetchall()]

    def ingredient_usage_totals(self) -> list[tuple[str, float, str, float]]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT i.name,
                       COALESCE(SUM(u.quantity_base), 0) AS used_base,
                       i.display_unit,
                       i.conversion_to_base
                FROM inventory_items i
                LEFT JOIN ingredient_usage u ON i.id = u.inventory_item_id
                GROUP BY i.id
                ORDER BY i.name COLLATE NOCASE
                """
            )
            rows = cursor.fetchall()
        return [
            (
                row["name"],
                row["used_base"],
                row["display_unit"],
                row["conversion_to_base"],
            )
            for row in rows
        ]

    def count_pending_orders(self) -> int:
        return self.count_pending_vendor_orders() + self.count_pending_customer_orders()

    def get_all_settings(self) -> Dict[str, str]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("SELECT key, value FROM app_settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    def get_setting(self, key: str, default: str = "") -> str:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        self._connection.commit()

    def low_stock_items(self) -> list[InventoryItem]:
        return [item for item in self.get_inventory_items() if item.is_low]

    def close(self) -> None:
        self._connection.close()


__all__ = [
    "DatabaseManager",
    "InventoryItem",
    "Recipe",
    "RecipeIngredient",
    "RecipeStep",
    "Supplier",
    "VendorOrder",
    "CustomerOrder",
]
