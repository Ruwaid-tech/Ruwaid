"""Database layer for the Painting Tracker desktop application."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

DB_FILE = Path("painting_tracker.db")


class DatabaseManager:
    """Simple SQLite helper for all persistence operations."""

    def __init__(self, db_path: Path | str = DB_FILE) -> None:
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._initialize_database()

    def _initialize_database(self) -> None:
        cursor = self.connection.cursor()
        cursor.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS paintings (
                painting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT,
                storage_location TEXT,
                materials_used TEXT,
                image_path TEXT,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS ideas (
                idea_id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea_title TEXT NOT NULL,
                idea_details TEXT,
                date_added TEXT,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS materials (
                material_id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_name TEXT NOT NULL,
                quantity TEXT,
                notes TEXT,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
            """
        )
        self.connection.commit()
        self._ensure_default_user()

    def _ensure_default_user(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        count = cursor.fetchone()["total_users"]
        if count == 0:
            cursor.execute(
                "INSERT INTO users(username, password) VALUES (?, ?)",
                ("admin", "admin123"),
            )
            self.connection.commit()

    # --- users ---
    def validate_user(self, username: str, password: str) -> Optional[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username.strip(), password),
        )
        return cursor.fetchone()

    def update_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ? AND password = ?",
            (user_id, old_password),
        )
        existing = cursor.fetchone()
        if not existing:
            return False
        cursor.execute(
            "UPDATE users SET password = ? WHERE user_id = ?",
            (new_password, user_id),
        )
        self.connection.commit()
        return True

    # --- paintings CRUD ---
    def list_paintings(self, user_id: int) -> List[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT painting_id, title, description, status, storage_location, materials_used, image_path
            FROM paintings
            WHERE user_id = ?
            ORDER BY painting_id DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()

    def get_painting(self, painting_id: int, user_id: int) -> Optional[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM paintings WHERE painting_id = ? AND user_id = ?",
            (painting_id, user_id),
        )
        return cursor.fetchone()

    def add_painting(
        self,
        title: str,
        description: str,
        status: str,
        storage_location: str,
        materials_used: str,
        image_path: str,
        user_id: int,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO paintings(title, description, status, storage_location, materials_used, image_path, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, status, storage_location, materials_used, image_path, user_id),
        )
        self.connection.commit()

    def update_painting(
        self,
        painting_id: int,
        title: str,
        description: str,
        status: str,
        storage_location: str,
        materials_used: str,
        image_path: str,
        user_id: int,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE paintings
            SET title = ?, description = ?, status = ?, storage_location = ?, materials_used = ?, image_path = ?
            WHERE painting_id = ? AND user_id = ?
            """,
            (title, description, status, storage_location, materials_used, image_path, painting_id, user_id),
        )
        self.connection.commit()

    def delete_painting(self, painting_id: int, user_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "DELETE FROM paintings WHERE painting_id = ? AND user_id = ?",
            (painting_id, user_id),
        )
        self.connection.commit()

    # --- ideas CRUD ---
    def list_ideas(self, user_id: int) -> List[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT idea_id, idea_title, idea_details, date_added
            FROM ideas
            WHERE user_id = ?
            ORDER BY idea_id DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()

    def get_idea(self, idea_id: int, user_id: int) -> Optional[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM ideas WHERE idea_id = ? AND user_id = ?",
            (idea_id, user_id),
        )
        return cursor.fetchone()

    def add_idea(self, idea_title: str, idea_details: str, date_added: str, user_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO ideas(idea_title, idea_details, date_added, user_id) VALUES (?, ?, ?, ?)",
            (idea_title, idea_details, date_added, user_id),
        )
        self.connection.commit()

    def update_idea(self, idea_id: int, idea_title: str, idea_details: str, date_added: str, user_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE ideas
            SET idea_title = ?, idea_details = ?, date_added = ?
            WHERE idea_id = ? AND user_id = ?
            """,
            (idea_title, idea_details, date_added, idea_id, user_id),
        )
        self.connection.commit()

    def delete_idea(self, idea_id: int, user_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM ideas WHERE idea_id = ? AND user_id = ?", (idea_id, user_id))
        self.connection.commit()

    # --- materials CRUD ---
    def list_materials(self, user_id: int) -> List[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT material_id, material_name, quantity, notes
            FROM materials
            WHERE user_id = ?
            ORDER BY material_id DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()

    def get_material(self, material_id: int, user_id: int) -> Optional[sqlite3.Row]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM materials WHERE material_id = ? AND user_id = ?",
            (material_id, user_id),
        )
        return cursor.fetchone()

    def add_material(self, material_name: str, quantity: str, notes: str, user_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO materials(material_name, quantity, notes, user_id) VALUES (?, ?, ?, ?)",
            (material_name, quantity, notes, user_id),
        )
        self.connection.commit()

    def update_material(self, material_id: int, material_name: str, quantity: str, notes: str, user_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE materials
            SET material_name = ?, quantity = ?, notes = ?
            WHERE material_id = ? AND user_id = ?
            """,
            (material_name, quantity, notes, material_id, user_id),
        )
        self.connection.commit()

    def delete_material(self, material_id: int, user_id: int) -> None:
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM materials WHERE material_id = ? AND user_id = ?", (material_id, user_id))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
