import os
import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "arthub.db")

sample_artworks = [
    (
        "Portrait Muse",
        "Expressive portrait capturing calm confidence in soft light.",
        "https://via.placeholder.com/600x400?text=Portrait",
        "Portrait",
        4200.0,
        6,
    ),
    (
        "Emerald Garden",
        "Lush floral watercolor with layered emerald greens.",
        "https://via.placeholder.com/600x400?text=Garden",
        "Floral",
        2600.0,
        8,
    ),
    (
        "Seaside Calm",
        "Gentle seascape in cool teal gradients and soft foam.",
        "https://via.placeholder.com/600x400?text=Seaside",
        "Seascape",
        3100.0,
        5,
    ),
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS order_lines;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS artworks;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS settings;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE artworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL UNIQUE,
            buyer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE order_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            artwork_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY(artwork_id) REFERENCES artworks(id) ON DELETE CASCADE
        );

        CREATE TABLE settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            alt_phone TEXT,
            about_content TEXT NOT NULL
        );
        """
    )

    # Seed admin
    cur.execute(
        "INSERT INTO users (full_name, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (
            "Site Administrator",
            "admin",
            "admin@example.com",
            generate_password_hash("Admin@123"),
            "ADMIN",
        ),
    )

    # Seed clients
    cur.execute(
        "INSERT INTO users (full_name, username, email, password_hash, role) VALUES (?, ?, ?, ?, 'CLIENT')",
        (
            "Lena Rivers",
            "lena",
            "lena@example.com",
            generate_password_hash("Password1!"),
        ),
    )
    cur.execute(
        "INSERT INTO users (full_name, username, email, password_hash, role) VALUES (?, ?, ?, ?, 'CLIENT')",
        (
            "Marco Silva",
            "marco",
            "marco@example.com",
            generate_password_hash("Password2!"),
        ),
    )

    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    for art in sample_artworks:
        cur.execute(
            "INSERT INTO artworks (title, description, image_url, category, price, stock, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (*art, now),
        )

    cur.execute(
        "INSERT INTO settings (owner_name, phone, alt_phone, about_content) VALUES (?, ?, ?, ?)",
        (
            "Art Hub Studio",
            "+49 555 1234567",
            "+49 555 9876543",
            "Welcome to Art Hub, a vibrant online space featuring curated works and bespoke commissions crafted with care.",
        ),
    )

    conn.commit()
    conn.close()
    print("Database initialized")


if __name__ == "__main__":
    init_db()
