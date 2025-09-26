"""Database management module for the Kitchen Manager application.

This module encapsulates all interactions with the SQLite database including
initialisation, CRUD helpers for the key entities (users, inventory items,
recipes and cooking logs) and higher-level analytics helpers used when
generating reports.
"""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Tuple


DB_PATH = Path("kitchen_manager.db")


def hash_password(password: str) -> str:
    """Return a SHA-256 hash of ``password`` suitable for storage."""

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@dataclass
class InventoryItem:
    id: int
    name: str
    quantity: float
    display_quantity: float
    unit: str
    display_unit: str
    min_quantity: float
    base_unit: str


class DatabaseManager:
    """High-level helper that wraps the SQLite connection and schema."""

    UNIT_CONVERSIONS: Dict[str, Tuple[str, float]] = {
        "g": ("g", 1.0),
        "kg": ("g", 1000.0),
        "ml": ("ml", 1.0),
        "l": ("ml", 1000.0),
        "unit": ("unit", 1.0),
        "units": ("unit", 1.0),
    }

    DISPLAY_UNITS: Dict[str, Tuple[str, float]] = {
        "g": ("kg", 1000.0),
        "ml": ("l", 1000.0),
    }

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                );

                CREATE TABLE IF NOT EXISTS inventory_item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    base_unit TEXT NOT NULL,
                    quantity REAL NOT NULL DEFAULT 0,
                    min_quantity REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS recipe (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS recipe_step (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
                    step_number INTEGER NOT NULL,
                    instruction TEXT NOT NULL,
                    UNIQUE(recipe_id, step_number)
                );

                CREATE TABLE IF NOT EXISTS recipe_ingredient (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
                    inventory_item_id INTEGER NOT NULL REFERENCES inventory_item(id),
                    quantity REAL NOT NULL,
                    UNIQUE(recipe_id, inventory_item_id)
                );

                CREATE TABLE IF NOT EXISTS consumption_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL REFERENCES recipe(id),
                    cooked_at TEXT NOT NULL
                );
                """
            )

    # ------------------------------------------------------------------
    # User management

    def register_user(self, username: str, password: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO user (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hash_password(password), datetime.utcnow().isoformat()),
            )

    def authenticate_user(self, username: str, password: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, password_hash FROM user WHERE username = ?",
                (username,),
            ).fetchone()
            if not row:
                return False
            if row["password_hash"] != hash_password(password):
                return False
            conn.execute(
                "UPDATE user SET last_login = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), row["id"]),
            )
        return True

    # ------------------------------------------------------------------
    # Inventory helpers

    def _convert_to_base(self, quantity: float, unit: str) -> Tuple[float, str]:
        if unit not in self.UNIT_CONVERSIONS:
            raise ValueError(f"Unsupported unit: {unit}")
        base_unit, multiplier = self.UNIT_CONVERSIONS[unit]
        return quantity * multiplier, base_unit

    def _format_quantity(self, quantity: float, base_unit: str) -> Tuple[float, str]:
        display_unit = base_unit
        display_quantity = quantity
        if base_unit in self.DISPLAY_UNITS and quantity >= self.DISPLAY_UNITS[base_unit][1]:
            display_unit, divisor = self.DISPLAY_UNITS[base_unit]
            display_quantity = quantity / divisor
        return display_quantity, display_unit

    def convert_quantity(self, quantity: float, unit: str, expected_base: str) -> float:
        base_quantity, base_unit = self._convert_to_base(quantity, unit)
        if base_unit != expected_base:
            raise ValueError("Unit mismatch for ingredient")
        return base_quantity

    def format_quantity(self, quantity: float, base_unit: str) -> Tuple[float, str]:
        return self._format_quantity(quantity, base_unit)

    def add_inventory_item(
        self, name: str, quantity: float, unit: str, min_quantity: float
    ) -> None:
        base_quantity, base_unit = self._convert_to_base(quantity, unit)
        min_quantity_base, min_unit = self._convert_to_base(min_quantity, unit)
        if min_unit != base_unit:
            raise ValueError("Minimum quantity unit mismatch")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO inventory_item (name, base_unit, quantity, min_quantity, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, base_unit, base_quantity, min_quantity_base, datetime.utcnow().isoformat()),
            )

    def update_inventory_quantity(self, item_id: int, quantity: float, unit: str) -> None:
        base_quantity, base_unit = self._convert_to_base(quantity, unit)
        with self.connect() as conn:
            row = conn.execute(
                "SELECT base_unit FROM inventory_item WHERE id = ?",
                (item_id,),
            ).fetchone()
            if not row:
                raise ValueError("Inventory item not found")
            if row["base_unit"] != base_unit:
                raise ValueError("Unit mismatch for update")
            conn.execute(
                "UPDATE inventory_item SET quantity = ? WHERE id = ?",
                (base_quantity, item_id),
            )

    def adjust_inventory_quantity(self, item_id: int, delta: float) -> None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT quantity FROM inventory_item WHERE id = ?",
                (item_id,),
            ).fetchone()
            if not row:
                raise ValueError("Inventory item not found")
            new_quantity = max(row["quantity"] + delta, 0.0)
            conn.execute(
                "UPDATE inventory_item SET quantity = ? WHERE id = ?",
                (new_quantity, item_id),
            )

    def delete_inventory_item(self, item_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM inventory_item WHERE id = ?", (item_id,))

    def fetch_inventory_items(self) -> List[InventoryItem]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, quantity, base_unit, min_quantity FROM inventory_item ORDER BY name"
            ).fetchall()
        items: List[InventoryItem] = []
        for row in rows:
            display_quantity, display_unit = self._format_quantity(row["quantity"], row["base_unit"])
            items.append(
                InventoryItem(
                    id=row["id"],
                    name=row["name"],
                    quantity=row["quantity"],
                    display_quantity=display_quantity,
                    unit=row["base_unit"],
                    display_unit=display_unit,
                    min_quantity=row["min_quantity"],
                    base_unit=row["base_unit"],
                )
            )
        return items

    def low_stock_items(self) -> List[InventoryItem]:
        return [item for item in self.fetch_inventory_items() if item.quantity <= item.min_quantity]

    # ------------------------------------------------------------------
    # Recipe helpers

    def add_recipe(self, name: str, description: str, steps: List[str]) -> int:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO recipe (name, description, created_at) VALUES (?, ?, ?)",
                (name, description, datetime.utcnow().isoformat()),
            )
            recipe_id = cur.lastrowid
            for index, step in enumerate(steps, start=1):
                cur.execute(
                    "INSERT INTO recipe_step (recipe_id, step_number, instruction) VALUES (?, ?, ?)",
                    (recipe_id, index, step.strip()),
                )
        return recipe_id

    def add_recipe_ingredient(
        self, recipe_id: int, inventory_item_id: int, quantity: float
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO recipe_ingredient (recipe_id, inventory_item_id, quantity)
                VALUES (?, ?, ?)
                """,
                (recipe_id, inventory_item_id, quantity),
            )

    def delete_recipe(self, recipe_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM recipe WHERE id = ?", (recipe_id,))

    def fetch_recipes(self) -> List[sqlite3.Row]:
        with self.connect() as conn:
            recipes = conn.execute(
                "SELECT id, name, description FROM recipe ORDER BY name"
            ).fetchall()
            return recipes

    def fetch_recipe_steps(self, recipe_id: int) -> List[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT instruction FROM recipe_step
                WHERE recipe_id = ?
                ORDER BY step_number
                """,
                (recipe_id,),
            ).fetchall()
        return [row["instruction"] for row in rows]

    def fetch_recipe_ingredients(
        self, recipe_id: int
    ) -> List[Tuple[int, str, float, str]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT ii.id, ii.name, ri.quantity, ii.base_unit
                FROM recipe_ingredient AS ri
                JOIN inventory_item AS ii ON ii.id = ri.inventory_item_id
                WHERE ri.recipe_id = ?
                ORDER BY ii.name
                """,
                (recipe_id,),
            ).fetchall()
        ingredients: List[Tuple[int, str, float, str]] = []
        for row in rows:
            ingredients.append((row["id"], row["name"], row["quantity"], row["base_unit"]))
        return ingredients

    # ------------------------------------------------------------------
    # Cooking and reporting

    def has_sufficient_inventory(self, recipe_id: int) -> Tuple[bool, List[str]]:
        shortages: List[str] = []
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT ii.name, ii.quantity, ri.quantity AS required
                FROM recipe_ingredient AS ri
                JOIN inventory_item AS ii ON ii.id = ri.inventory_item_id
                WHERE ri.recipe_id = ?
                """,
                (recipe_id,),
            ).fetchall()
        for row in rows:
            if row["quantity"] < row["required"]:
                shortages.append(f"{row['name']} (need {row['required'] - row['quantity']:.1f} more)")
        return (len(shortages) == 0, shortages)

    def consume_recipe(self, recipe_id: int) -> None:
        sufficient, shortages = self.has_sufficient_inventory(recipe_id)
        if not sufficient:
            shortage_list = ", ".join(shortages)
            raise ValueError(f"Insufficient inventory: {shortage_list}")
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO consumption_log (recipe_id, cooked_at) VALUES (?, ?)",
                (recipe_id, datetime.utcnow().isoformat()),
            )
            ingredients = conn.execute(
                "SELECT inventory_item_id, quantity FROM recipe_ingredient WHERE recipe_id = ?",
                (recipe_id,),
            ).fetchall()
            for ingredient in ingredients:
                conn.execute(
                    "UPDATE inventory_item SET quantity = MAX(quantity - ?, 0) WHERE id = ?",
                    (ingredient["quantity"], ingredient["inventory_item_id"]),
                )

    def recipe_statistics(self) -> List[Tuple[str, int]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT r.name, COUNT(c.id) AS times_cooked
                FROM recipe AS r
                LEFT JOIN consumption_log AS c ON c.recipe_id = r.id
                GROUP BY r.id
                ORDER BY r.name
                """
            ).fetchall()
        return [(row["name"], row["times_cooked"]) for row in rows]

    def ingredient_usage_statistics(self) -> List[Tuple[str, float, str]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT ii.name, ii.base_unit, SUM(ri.quantity * cooked.count) AS total_used
                FROM recipe_ingredient AS ri
                JOIN inventory_item AS ii ON ii.id = ri.inventory_item_id
                JOIN (
                    SELECT recipe_id, COUNT(*) AS count
                    FROM consumption_log
                    GROUP BY recipe_id
                ) AS cooked ON cooked.recipe_id = ri.recipe_id
                GROUP BY ii.id
                ORDER BY ii.name
                """
            ).fetchall()
        usage: List[Tuple[str, float, str]] = []
        for row in rows:
            display_quantity, display_unit = self.format_quantity(row["total_used"] or 0.0, row["base_unit"])
            usage.append((row["name"], display_quantity, display_unit))
        return usage


__all__ = ["DatabaseManager", "InventoryItem"]

