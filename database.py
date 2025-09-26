"""SQLite data layer for the Kitchen Manager desktop application."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

DB_PATH = Path("kitchen_manager.db")


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


class DatabaseManager:
    """High level helper that encapsulates all persistence operations."""

    def __init__(self, path: Path | str = DB_PATH) -> None:
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._initialise_schema()

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
                """
            )
            self._connection.commit()

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
]
