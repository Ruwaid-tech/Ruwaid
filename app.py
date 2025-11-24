import base64
import os
import re
import sqlite3
import sys
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
DEFAULT_IMAGE_RELATIVE = os.path.join("images", "default_placeholder.png")
DEFAULT_IMAGE_PATH = os.path.join(IMAGES_DIR, "default_placeholder.png")
DB_PATH = "art_hub.db"


# 1x1 PNG pixel; valid base64 with correct padding to avoid decode errors
PLACEHOLDER_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAwMB/alyWpwAAAAASUVORK5CYII="
)


def ensure_placeholder_assets() -> None:
    """Create lightweight placeholder PNGs as text-only assets to avoid binary commits."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    image_names = [
        "default_placeholder.png",
        "waves.png",
        "floral_bloom.png",
        "city_lines.png",
        "monsoon.png",
        "terracotta.png",
        "aurora.png",
        "heritage_door.png",
        "lotus_study.png",
        "sunset_ridge.png",
        "quiet_river.png",
    ]
    data = base64.b64decode(PLACEHOLDER_BASE64)
    for name in image_names:
        dest = os.path.join(IMAGES_DIR, name)
        if not os.path.exists(dest):
            with open(dest, "wb") as f:
                f.write(data)


@dataclass
class User:
    id: int
    email: str
    role: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def resolve_image_path(path: Optional[str]) -> str:
    """Return an absolute image path with a safe fallback placeholder."""
    if path and path.strip():
        candidate = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
        if os.path.exists(candidate):
            return candidate
    return DEFAULT_IMAGE_PATH


class DatabaseManager:
    """Responsible for schema creation and seeding."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        ensure_placeholder_assets()
        self._ensure_db()
        self.users = UserRepo(db_path)
        self.artworks = ArtworkRepo(db_path)
        self.orders = OrderRepo(db_path)
        self.settings = SettingsRepo(db_path)

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'buyer')),
                    name TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS artworks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT,
                    price REAL NOT NULL,
                    image_path TEXT,
                    stock INTEGER NOT NULL DEFAULT 0,
                    description TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buyer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS order_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    artwork_id INTEGER NOT NULL REFERENCES artworks(id),
                    qty INTEGER NOT NULL,
                    unit_price REAL NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    owner_name TEXT NOT NULL,
                    owner_phone TEXT NOT NULL,
                    alt_phone TEXT
                )
                """
            )
            conn.commit()
            cur.execute("PRAGMA table_info(settings)")
            cols = [r[1] for r in cur.fetchall()]
            if "alt_phone" not in cols:
                cur.execute("ALTER TABLE settings ADD COLUMN alt_phone TEXT")
            conn.commit()
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO users (email, password_hash, role, name) VALUES (?, ?, 'admin', ?)",
                    ("admin@arthub.com", hash_password("admin123"), "Admin"),
                )
                cur.execute(
                    "INSERT INTO users (email, password_hash, role, name) VALUES (?, ?, 'buyer', ?)",
                    ("buyer@arthub.com", hash_password("buyer123"), "Buyer"),
                )
            cur.execute("SELECT COUNT(*) FROM settings")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO settings (id, owner_name, owner_phone, alt_phone) VALUES (1, ?, ?, ?)",
                    ("Ms. Priya Sharma", "+91-98XXXXXXX5", "+91-80XXXXXXXX"),
                )
            cur.execute("SELECT COUNT(*) FROM artworks")
            image_map = {
                "Waves": os.path.join("images", "waves.png"),
                "Floral Bloom": os.path.join("images", "floral_bloom.png"),
                "City Lines": os.path.join("images", "city_lines.png"),
                "Monsoon": os.path.join("images", "monsoon.png"),
                "Terracotta": os.path.join("images", "terracotta.png"),
                "Aurora": os.path.join("images", "aurora.png"),
                "Heritage Door": os.path.join("images", "heritage_door.png"),
                "Lotus Study": os.path.join("images", "lotus_study.png"),
                "Sunset Ridge": os.path.join("images", "sunset_ridge.png"),
                "Quiet River": os.path.join("images", "quiet_river.png"),
            }
            if cur.fetchone()[0] == 0:
                sample_artworks = [
                    ("Waves", "Seascape", 1500.0, image_map["Waves"], 12, "Ink on paper celebrating tidal rhythms."),
                    ("Floral Bloom", "Floral", 1800.0, image_map["Floral Bloom"], 8, "Layered gouache petals with soft gradients."),
                    ("City Lines", "Urban", 1400.0, image_map["City Lines"], 10, "Minimal skyline rendered with gold ink."),
                    ("Monsoon", "Seascape", 1650.0, image_map["Monsoon"], 6, "Stormy clouds over a quiet harbour."),
                    ("Terracotta", "Abstract", 1100.0, image_map["Terracotta"], 9, "Earthy tones with textured brushwork."),
                    ("Aurora", "Abstract", 2100.0, image_map["Aurora"], 5, "Bright ribbons of light across a dark sky."),
                    ("Heritage Door", "Urban", 950.0, image_map["Heritage Door"], 7, "Detailed doorway from old Chennai quarters."),
                    ("Lotus Study", "Floral", 1200.0, image_map["Lotus Study"], 10, "Pencil and watercolor botanical notes."),
                    ("Sunset Ridge", "Landscape", 1750.0, image_map["Sunset Ridge"], 11, "Warm light on distant ridgelines."),
                    ("Quiet River", "Landscape", 1600.0, image_map["Quiet River"], 13, "Evening reflections with soft ripples."),
                ]
                cur.executemany(
                    "INSERT INTO artworks (title, category, price, image_path, stock, description) VALUES (?, ?, ?, ?, ?, ?)",
                    sample_artworks,
                )
            # Backfill images for existing records missing image paths
            cur.execute("SELECT id, title, image_path FROM artworks")
            for art_id, title, path in cur.fetchall():
                if (not path or path.strip() == "") and title in image_map:
                    cur.execute("UPDATE artworks SET image_path=? WHERE id=?", (image_map[title], art_id))
            conn.commit()



class UserRepo:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def validate_user(self, email: str, password: str) -> Optional[User]:
        hashed = hash_password(password)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, email, role FROM users WHERE email=? AND password_hash=?",
                (email, hashed),
            )
            row = cur.fetchone()
            if row:
                return User(id=row[0], email=row[1], role=row[2])
        return None

    def user_exists(self, email: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM users WHERE email=?", (email,))
            return cur.fetchone() is not None

    def create_buyer(self, name: str, email: str, password: str) -> int:
        if not email or not password:
            raise ValueError("Email and password are required")
        if self.user_exists(email):
            raise ValueError("An account already exists for this email")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (email, password_hash, role, name) VALUES (?, ?, 'buyer', ?)",
                (email, hash_password(password), name or ""),
            )
            conn.commit()
            return cur.lastrowid


class ArtworkRepo:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_artworks(self, search: str = "", category: str = "All", sort: str = "Price") -> List[Tuple]:
        query = "SELECT id, title, category, price, stock, description, image_path FROM artworks"
        filters: List[str] = []
        params: List[str] = []
        if search:
            filters.append("title LIKE ?")
            params.append(f"%{search}%")
        if category and category != "All":
            filters.append("category = ?")
            params.append(category)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        if sort == "Price ↓":
            query += " ORDER BY price DESC"
        else:
            query += " ORDER BY price ASC"
        with sqlite3.connect(self.db_path) as conn:
            return conn.cursor().execute(query, params).fetchall()

    def get_categories(self) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.cursor().execute(
                "SELECT DISTINCT category FROM artworks WHERE category IS NOT NULL"
            ).fetchall()
        categories = [r[0] for r in rows if r[0]]
        return ["All"] + sorted(categories)

    def get_artwork(self, artwork_id: int) -> Optional[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, category, price, stock, description, image_path FROM artworks WHERE id=?",
                (artwork_id,),
            )
            return cur.fetchone()

    def upsert_artwork(
        self, artwork_id: Optional[int], title: str, category: str, price: float, stock: int, description: str
    ) -> None:
        fallback_path = DEFAULT_IMAGE_RELATIVE
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            if artwork_id:
                cur.execute("SELECT image_path FROM artworks WHERE id=?", (artwork_id,))
                existing = cur.fetchone()
                image_path = existing[0] if existing and existing[0] else fallback_path
                cur.execute(
                    "UPDATE artworks SET title=?, category=?, price=?, stock=?, description=?, image_path=? WHERE id=?",
                    (title, category, price, stock, description, image_path, artwork_id),
                )
            else:
                cur.execute(
                    "INSERT INTO artworks (title, category, price, stock, image_path, description) VALUES (?, ?, ?, ?, ?, ?)",
                    (title, category, price, stock, fallback_path, description),
                )
            conn.commit()

    def delete_artwork(self, artwork_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("DELETE FROM artworks WHERE id=?", (artwork_id,))
            conn.commit()


class OrderRepo:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create_order(self, buyer_name: str, phone: str, address: str, cart: Dict[int, int]) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            for art_id, qty in cart.items():
                cur.execute("SELECT stock FROM artworks WHERE id=?", (art_id,))
                row = cur.fetchone()
                if not row or row[0] < qty:
                    raise ValueError("Insufficient stock for selected artworks")
            cur.execute(
                "INSERT INTO orders (buyer_name, phone, address, status) VALUES (?, ?, ?, ?)",
                (buyer_name, phone, address, "Pending COD"),
            )
            order_id = cur.lastrowid
            for art_id, qty in cart.items():
                cur.execute("SELECT price FROM artworks WHERE id=?", (art_id,))
                price = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO order_lines (order_id, artwork_id, qty, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, art_id, qty, price),
                )
                cur.execute("UPDATE artworks SET stock = stock - ? WHERE id=?", (qty, art_id))
            conn.commit()
            return order_id

    def get_order_details(self, order_id: int) -> Tuple:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, buyer_name, phone, address, status, created_at FROM orders WHERE id=?",
                (order_id,),
            )
            order = cur.fetchone()
            cur.execute(
                """
                SELECT artworks.title, order_lines.qty
                FROM order_lines
                JOIN artworks ON artworks.id = order_lines.artwork_id
                WHERE order_lines.order_id=?
                """,
                (order_id,),
            )
            lines = cur.fetchall()
            return order, lines

    def fetch_notifications(self) -> List[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT orders.id, orders.buyer_name, orders.phone, orders.address, orders.status, orders.created_at,
                       GROUP_CONCAT(artworks.title || ' x' || order_lines.qty, ', ')
                FROM orders
                LEFT JOIN order_lines ON order_lines.order_id = orders.id
                LEFT JOIN artworks ON artworks.id = order_lines.artwork_id
                WHERE orders.status = 'Pending COD'
                GROUP BY orders.id
                ORDER BY orders.created_at DESC
                """
            )
            return cur.fetchall()

    def fetch_order_history(self) -> List[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT orders.id, orders.buyer_name, orders.phone, orders.address, orders.status, orders.created_at,
                       GROUP_CONCAT(artworks.title || ' x' || order_lines.qty, ', ')
                FROM orders
                LEFT JOIN order_lines ON order_lines.order_id = orders.id
                LEFT JOIN artworks ON artworks.id = order_lines.artwork_id
                GROUP BY orders.id
                ORDER BY orders.created_at DESC
                """
            )
            return cur.fetchall()

    def mark_contacted(self, order_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("UPDATE orders SET status='Contacted' WHERE id=?", (order_id,))
            conn.commit()

    def metrics(self) -> Tuple[int, int, float]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), SUM(CASE WHEN status='Pending COD' THEN 1 ELSE 0 END) FROM orders")
            total, pending = cur.fetchone()
            cur.execute(
                "SELECT SUM(order_lines.qty * order_lines.unit_price) FROM order_lines"
            )
            revenue = cur.fetchone()[0] or 0.0
            return total or 0, pending or 0, revenue


class SettingsRepo:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_settings(self) -> Tuple[str, str, str]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT owner_name, owner_phone, COALESCE(alt_phone, '') FROM settings WHERE id=1")
            row = cur.fetchone()
            return row if row else ("", "", "")

    def update_settings(self, owner_name: str, owner_phone: str, alt_phone: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute(
                "UPDATE settings SET owner_name=?, owner_phone=?, alt_phone=? WHERE id=1",
                (owner_name, owner_phone, alt_phone),
            )
            conn.commit()


class NotificationManager:
    def __init__(self):
        self.entries: List[str] = []

    def push_new_order(self, order_id: int, buyer: str, phone: str, address: str, items: str) -> None:
        message = f"⚠ NEW ORDER {order_id}: {buyer} | {phone} | {address} | {items}"
        self.entries.insert(0, message)

    def recent(self) -> List[str]:
        return list(self.entries)


class DetailUI(QDialog):
    add_with_qty = pyqtSignal(int, int)

    def __init__(self, art: Tuple, parent: QWidget | None = None):
        super().__init__(parent)
        self.art = art
        self.setWindowTitle("ART HUB — Artwork Detail")
        layout = QVBoxLayout()

        header = QLabel("ART HUB – Artwork Detail")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-family: 'Courier New'; font-weight: 700;")
        layout.addWidget(header)

        body = QGridLayout()
        image = QLabel()
        image.setFixedSize(220, 180)
        pix = QPixmap(resolve_image_path(self.art[6]))
        if pix.isNull():
            image.setText("[Large Image]")
            image.setAlignment(Qt.AlignCenter)
            image.setStyleSheet("border: 1px dashed #aaa;")
        else:
            image.setPixmap(pix.scaled(image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        body.addWidget(image, 0, 0, 3, 1)

        body.addWidget(QLabel(f"Title: {self.art[1]}"), 0, 1)
        body.addWidget(QLabel(f"Price: ₹{self.art[3]:.0f}"), 1, 1)
        body.addWidget(QLabel(f"In Stock: {self.art[4]}"), 1, 2)
        desc = QLabel(self.art[5] or "No description yet.")
        desc.setWordWrap(True)
        body.addWidget(desc, 2, 1, 1, 2)
        qty_row = QHBoxLayout()
        qty_row.addWidget(QLabel("Qty:"))
        self.qty = QSpinBox()
        self.qty.setMinimum(1)
        self.qty.setMaximum(max(1, self.art[4]))
        qty_row.addWidget(self.qty)
        body.addLayout(qty_row, 3, 1)
        layout.addLayout(body)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add to Cart")
        add_btn.setEnabled(self.art[4] > 0)
        add_btn.clicked.connect(self._add)
        back_btn = QPushButton("Back to Gallery")
        back_btn.clicked.connect(self.reject)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(back_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def _add(self) -> None:
        self.add_with_qty.emit(self.art[0], self.qty.value())
        self.accept()


class ContactDialogUI(QDialog):
    def __init__(self, owner_name: str, owner_phone: str, alt_phone: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Contact Owner")
        layout = QVBoxLayout()

        header = QLabel("✓ Order Recorded")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-family: 'Courier New'; font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        card = QFrame()
        card.setStyleSheet(
            "QFrame { border: 1px solid #444; border-radius: 8px; padding: 14px; background: #f8fbff; font-family: 'Courier New'; }"
        )
        info = QVBoxLayout()
        info.addWidget(QLabel("Please contact the owner to finalize COD."))
        info.addWidget(QLabel(f"Owner: {owner_name}"))
        info.addWidget(QLabel(f"Phone: {owner_phone}"))
        if alt_phone:
            info.addWidget(QLabel(f"Alt: {alt_phone}"))
        card.setLayout(info)
        layout.addWidget(card)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton("Copy Phone")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(owner_phone))
        close_btn = QPushButton("OK")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)


class OrderConfirmationDialog(QDialog):
    def __init__(self, order_id: int, owner_phone: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Order Confirmation")
        layout = QVBoxLayout()
        title = QLabel("🎉 Thank You!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        card = QFrame()
        card.setStyleSheet(
            "QFrame { border: 1px dashed #666; border-radius: 8px; padding: 12px; font-family: 'Courier New'; background: #fff; }"
        )
        info = QVBoxLayout()
        info.addWidget(QLabel(f"Order ID: ORD-{order_id:04d}"))
        info.addWidget(QLabel("Status: Pending COD"))
        info.addWidget(QLabel(f"Next: Call {owner_phone} to coordinate delivery."))
        card.setLayout(info)
        layout.addWidget(card)
        close_btn = QPushButton("Back to Gallery")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.setLayout(layout)


class CheckoutUI(QDialog):
    order_completed = pyqtSignal(int)

    def __init__(self, orders: OrderRepo, artworks: ArtworkRepo, settings: SettingsRepo, cart: Dict[int, int], parent: QWidget | None = None):
        super().__init__(parent)
        self.orders = orders
        self.artworks = artworks
        self.settings = settings
        self.cart = cart
        self.setWindowTitle("ART HUB – Checkout")
        layout = QVBoxLayout()

        cart_box = QGroupBox("CART")
        cart_box.setStyleSheet("QGroupBox { font-weight: 700; font-family: 'Courier New'; }")
        cart_layout = QVBoxLayout()
        self.cart_summary = QLabel()
        self.cart_summary.setStyleSheet("font-family: 'Courier New';")
        cart_layout.addWidget(self.cart_summary)
        cart_box.setLayout(cart_layout)
        layout.addWidget(cart_box)

        form_box = QGroupBox("BUYER DETAILS")
        form_box.setStyleSheet("QGroupBox { font-weight: 700; font-family: 'Courier New'; }")
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QTextEdit()
        self.phone_input.setPlaceholderText("+9198XXXXXXXX")
        self.address_input.setPlaceholderText("Flat / Street / City")
        form.addRow("Name", self.name_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Address", self.address_input)
        form_box.setLayout(form)
        layout.addWidget(form_box)

        payment_label = QLabel("Payment: (•) Cash on Delivery")
        layout.addWidget(payment_label)

        btn_row = QHBoxLayout()
        confirm_btn = QPushButton("Confirm Order")
        confirm_btn.clicked.connect(self.handle_confirm)
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.reject)
        btn_row.addWidget(confirm_btn)
        btn_row.addWidget(back_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)
        self.refresh_summary()

    def refresh_summary(self) -> None:
        parts = []
        for art_id, qty in self.cart.items():
            art = self.artworks.get_artwork(art_id)
            if art:
                parts.append(f"{art[1]} × {qty} – ₹{art[3] * qty:.0f}")
        self.cart_summary.setText("\n".join(parts))

    def handle_confirm(self) -> None:
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()
        if not name or not phone or not address:
            QMessageBox.warning(self, "Missing details", "Please fill in name, phone, and address.")
            return
        if not PHONE_REGEX.match(phone):
            QMessageBox.warning(self, "Phone", "Please enter a valid phone in E.164 format (e.g., +919900000000).")
            return
        try:
            order_id = self.orders.create_order(name, phone, address, self.cart)
        except ValueError as exc:
            QMessageBox.warning(self, "Stock issue", str(exc))
            return
        self.order_completed.emit(order_id)
        self.accept()


class SignupDialog(QDialog):
    registered = pyqtSignal(User)

    def __init__(self, users: UserRepo, parent: QWidget | None = None):
        super().__init__(parent)
        self.users = users
        self.setWindowTitle("Create Account")
        layout = QVBoxLayout()
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form.addRow("Name", self.name_input)
        form.addRow("Email", self.email_input)
        form.addRow("Password", self.password_input)
        layout.addLayout(form)
        btn = QPushButton("Sign up")
        btn.clicked.connect(self.handle_signup)
        layout.addWidget(btn)
        self.setLayout(layout)

    def handle_signup(self) -> None:
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not EMAIL_REGEX.match(email):
            QMessageBox.warning(self, "Email", "Please enter a valid email address.")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Weak password", "Please use at least 6 characters.")
            return
        try:
            self.users.create_buyer(name, email, password)
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot create account", str(exc))
            return
        user = self.users.validate_user(email, password)
        if user:
            self.registered.emit(user)
            QMessageBox.information(self, "Welcome", "Account created. You are now signed in.")
            self.accept()


class CartDialog(QDialog):
    checkout_requested = pyqtSignal()

    def __init__(self, artworks: ArtworkRepo, cart: Dict[int, int], parent: QWidget | None = None):
        super().__init__(parent)
        self.artworks = artworks
        self.cart = cart
        self.setWindowTitle("Cart")
        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Artwork", "Price", "Qty", "Remove"])
        self.layout.addWidget(self.table)
        btn_row = QHBoxLayout()
        self.checkout_btn = QPushButton("Checkout")
        self.checkout_btn.clicked.connect(self._on_checkout)
        btn_row.addWidget(self.checkout_btn)
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.reject)
        btn_row.addWidget(back_btn)
        self.layout.addLayout(btn_row)
        self.setLayout(self.layout)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(0)
        for row_idx, (art_id, qty) in enumerate(self.cart.items()):
            art = self.artworks.get_artwork(art_id)
            if not art:
                continue
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(art[1]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(f"₹{art[3]:.0f}"))
            spin = QSpinBox()
            spin.setValue(qty)
            spin.setMinimum(1)
            spin.setMaximum(max(1, art[4]))
            spin.valueChanged.connect(lambda value, a_id=art_id: self._update_qty(a_id, value))
            self.table.setCellWidget(row_idx, 2, spin)
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda _, a_id=art_id: self._remove(a_id))
            self.table.setCellWidget(row_idx, 3, remove_btn)

    def _update_qty(self, art_id: int, qty: int) -> None:
        self.cart[art_id] = qty

    def _remove(self, art_id: int) -> None:
        self.cart.pop(art_id, None)
        self.refresh()

    def _on_checkout(self) -> None:
        if not self.cart:
            QMessageBox.information(self, "Empty cart", "Add artworks before checking out.")
            return
        self.checkout_requested.emit()
        self.accept()


class GalleryUI(QWidget):
    add_to_cart = pyqtSignal(int, int)
    open_cart = pyqtSignal()

    def __init__(self, artworks: ArtworkRepo):
        super().__init__()
        self.artworks = artworks
        layout = QVBoxLayout()
        header = QLabel("ART HUB – Gallery")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-weight: 700; font-size: 16px; font-family: 'Courier New';")
        layout.addWidget(header)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        controls.addWidget(self.search_input)
        controls.addWidget(QLabel("Category:"))
        self.category_box = QComboBox()
        controls.addWidget(self.category_box)
        controls.addWidget(QLabel("Sort:"))
        self.sort_box = QComboBox()
        self.sort_box.addItems(["Price ↑", "Price ↓"])
        controls.addWidget(self.sort_box)
        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self.refresh)
        controls.addWidget(filter_btn)
        self.cart_label = QPushButton("Cart (0)")
        self.cart_label.clicked.connect(self.open_cart.emit)
        checkout_btn = QPushButton("Checkout")
        checkout_btn.clicked.connect(self.open_cart.emit)
        controls.addWidget(self.cart_label)
        controls.addWidget(checkout_btn)
        layout.addLayout(controls)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        self.card_layout = QGridLayout()
        container.setLayout(self.card_layout)
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)
        self.setLayout(layout)
        self.refresh()

    def update_cart_count(self, count: int) -> None:
        self.cart_label.setText(f"Cart ({count})")

    def refresh(self) -> None:
        current_category = self.category_box.currentText()
        self.category_box.blockSignals(True)
        self.category_box.clear()
        categories = self.artworks.get_categories()
        self.category_box.addItems(categories)
        if current_category in categories:
            self.category_box.setCurrentText(current_category)
        self.category_box.blockSignals(False)

        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        search = self.search_input.text().strip()
        category = self.category_box.currentText() or "All"
        sort = self.sort_box.currentText() or "Price ↑"
        for idx, art in enumerate(self.artworks.get_artworks(search=search, category=category, sort=sort)):
            card = self._build_card(art)
            row = idx // 2
            col = idx % 2
            self.card_layout.addWidget(card, row, col)

    def _build_card(self, art: Tuple) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { border: 1px solid #ccc; border-radius: 8px; padding: 10px; background: #fdfdfd; font-family: 'Courier New'; }"
        )
        layout = QVBoxLayout()
        img = QLabel()
        img.setFixedSize(140, 100)
        pix = QPixmap(resolve_image_path(art[6]))
        if pix.isNull():
            img.setText("[Image]")
            img.setAlignment(Qt.AlignCenter)
            img.setStyleSheet("border: 1px dashed #aaa;")
        else:
            img.setPixmap(pix.scaled(img.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(img)
        title = QLabel(f"\"{art[1]}\"")
        price = QLabel(f"₹{art[3]:.0f} | Stock: {art[4]}")
        layout.addWidget(title)
        layout.addWidget(price)
        btn_row = QHBoxLayout()
        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(lambda _, a=art: self._open_detail(a))
        add_btn = QPushButton("Add to Cart")
        add_btn.setEnabled(art[4] > 0)
        add_btn.clicked.connect(lambda _, a_id=art[0]: self.add_to_cart.emit(a_id, 1))
        btn_row.addWidget(view_btn)
        btn_row.addWidget(add_btn)
        layout.addLayout(btn_row)
        frame.setLayout(layout)
        return frame

    def _open_detail(self, art: Tuple) -> None:
        dialog = DetailUI(art, self)
        dialog.add_with_qty.connect(self.add_to_cart.emit)
        dialog.exec_()


class LoginUI(QWidget):
    authenticated = pyqtSignal(User)

    def __init__(self, users: UserRepo):
        super().__init__()
        self.users = users
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("ART HUB – Login")
        title.setStyleSheet("font-size: 20px; font-weight: 700; font-family: 'Courier New';")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet(
            "QFrame { border: 1px dashed #4a4a4a; border-radius: 10px; padding: 20px; background: #fdfdfb; }"
        )
        card.setMaximumWidth(560)
        card_layout = QVBoxLayout()
        card_layout.setSpacing(14)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setContentsMargins(6, 6, 6, 6)
        form.setSpacing(10)

        form_wrapper = QWidget()
        form_wrapper.setLayout(form)
        form_wrapper.setStyleSheet(
            "QLabel { color: #1d1d1d; font-weight: 700; font-family: 'Courier New'; }"
            "QLineEdit { background: #ffffff; color: #111111; border: 1px solid #1e6bd6; padding: 9px; border-radius: 6px; font-family: 'Courier New'; }"
            "QLineEdit:focus { border: 2px solid #0e4ba8; }"
        )
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("you@example.com")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.show_box = QCheckBox("Show/Hide")
        self.show_box.stateChanged.connect(self._toggle_password)
        form.addRow("Email", self.email_input)
        form.addRow("Password", self.password_input)
        form.addRow("", self.show_box)
        card_layout.addWidget(form_wrapper)

        btn_row = QHBoxLayout()
        login_btn = QPushButton("Login")
        login_btn.setDefault(True)
        login_btn.clicked.connect(self.handle_login)
        signup_btn = QPushButton("Sign up")
        signup_btn.clicked.connect(self.open_signup)
        btn_row.addWidget(login_btn)
        btn_row.addWidget(signup_btn)
        card_layout.addLayout(btn_row)

        help_label = QLabel("Help: Trouble logging in? Contact owner.")
        help_label.setStyleSheet("color: #444; font-family: 'Courier New';")
        card_layout.addWidget(help_label)

        card.setLayout(card_layout)
        layout.addWidget(card)
        self.setLayout(layout)

    def handle_login(self) -> None:
        email = self.email_input.text().strip()
        if not EMAIL_REGEX.match(email):
            QMessageBox.warning(self, "Email", "Please enter a valid email address.")
            return
        user = self.users.validate_user(email, self.password_input.text())
        if user:
            self.authenticated.emit(user)
        else:
            QMessageBox.warning(self, "Login failed", "Invalid credentials. Try the defaults or create a new buyer account.")

    def _toggle_password(self, state: int) -> None:
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def open_signup(self) -> None:
        dialog = SignupDialog(self.users, self)
        dialog.registered.connect(self.authenticated.emit)
        dialog.exec_()


class AdminDashboard(QWidget):
    def __init__(self, orders: OrderRepo, notifications: NotificationManager):
        super().__init__()
        self.orders = orders
        self.notifications = notifications
        layout = QVBoxLayout()
        layout.addWidget(QLabel("ART HUB – Admin Dashboard"))
        self.list = QListWidget()
        layout.addWidget(QLabel("Notifications"))
        layout.addWidget(self.list)
        btn_row = QHBoxLayout()
        self.call_btn = QPushButton("Call Buyer")
        self.call_btn.clicked.connect(self.call_buyer)
        self.view_btn = QPushButton("View Order")
        self.view_btn.clicked.connect(self.view_order)
        self.mark_btn = QPushButton("Mark Contacted")
        self.mark_btn.clicked.connect(self.mark_contacted)
        btn_row.addWidget(self.call_btn)
        btn_row.addWidget(self.view_btn)
        btn_row.addWidget(self.mark_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for note in self.notifications.recent():
            self.list.addItem(note)
        for order in self.orders.fetch_notifications():
            item = QListWidgetItem(
                f"⚠ NEW ORDER {order[5]} – Buyer: {order[1]} | Ph: {order[2]} | Artwork: {order[6] or ''}"
            )
            item.setData(Qt.UserRole, order)
            self.list.addItem(item)

    def mark_contacted(self) -> None:
        item = self.list.currentItem()
        if not item:
            return
        order = item.data(Qt.UserRole)
        if not order:
            return
        self.orders.mark_contacted(order[0])
        self.refresh()

    def _selected_order(self) -> Optional[Tuple]:
        item = self.list.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def call_buyer(self) -> None:
        order = self._selected_order()
        if not order:
            return
        QMessageBox.information(self, "Call Buyer", f"Phone: {order[2]}\nAddress: {order[3]}")

    def view_order(self) -> None:
        order = self._selected_order()
        if not order:
            return
        QMessageBox.information(
            self,
            "Order Details",
            f"Order #{order[0]}\nBuyer: {order[1]}\nPhone: {order[2]}\nAddress: {order[3]}\nItems: {order[6] or ''}",
        )


class OrdersHistory(QWidget):
    def __init__(self, orders: OrderRepo):
        super().__init__()
        self.orders = orders
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Order", "Buyer", "Phone", "Address", "Status", "Items", "Created"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.refresh()

    def refresh(self) -> None:
        orders = self.orders.fetch_order_history()
        self.table.setRowCount(0)
        for idx, order in enumerate(orders):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(f"ORD-{order[0]:04d}"))
            self.table.setItem(idx, 1, QTableWidgetItem(order[1]))
            self.table.setItem(idx, 2, QTableWidgetItem(order[2]))
            self.table.setItem(idx, 3, QTableWidgetItem(order[3]))
            self.table.setItem(idx, 4, QTableWidgetItem(order[4]))
            self.table.setItem(idx, 5, QTableWidgetItem(order[6] or ""))
            self.table.setItem(idx, 6, QTableWidgetItem(order[5]))


class ArtworkCrud(QWidget):
    def __init__(self, artworks: ArtworkRepo):
        super().__init__()
        self.artworks = artworks
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Category", "Price", "Stock", "Description"])
        self.table.itemSelectionChanged.connect(self._fill_form)
        layout.addWidget(self.table)

        form = QFormLayout()
        self.id_label = QLabel("New")
        self.title_input = QLineEdit()
        self.category_input = QLineEdit()
        self.price_input = QLineEdit()
        self.price_input.setValidator(QIntValidator(0, 1000000))
        self.stock_input = QLineEdit()
        self.stock_input.setValidator(QIntValidator(0, 100000))
        self.description_input = QTextEdit()
        form.addRow("Editing", self.id_label)
        form.addRow("Title", self.title_input)
        form.addRow("Category", self.category_input)
        form.addRow("Price", self.price_input)
        form.addRow("Stock", self.stock_input)
        form.addRow("Description", self.description_input)
        layout.addLayout(form)
        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete)
        btns.addWidget(save_btn)
        btns.addWidget(delete_btn)
        layout.addLayout(btns)
        self.setLayout(layout)
        self.refresh()

    def refresh(self) -> None:
        artworks = self.artworks.get_artworks()
        self.table.setRowCount(0)
        for idx, art in enumerate(artworks):
            self.table.insertRow(idx)
            for col, value in enumerate(art[:6]):
                self.table.setItem(idx, col, QTableWidgetItem(str(value)))
        self._clear_form()

    def _clear_form(self) -> None:
        self.id_label.setText("New")
        self.title_input.clear()
        self.category_input.clear()
        self.price_input.clear()
        self.stock_input.clear()
        self.description_input.clear()

    def _fill_form(self) -> None:
        selected = self.table.currentRow()
        if selected < 0:
            return
        self.id_label.setText(self.table.item(selected, 0).text())
        self.title_input.setText(self.table.item(selected, 1).text())
        self.category_input.setText(self.table.item(selected, 2).text())
        self.price_input.setText(self.table.item(selected, 3).text().replace("₹", ""))
        self.stock_input.setText(self.table.item(selected, 4).text())
        self.description_input.setPlainText(self.table.item(selected, 5).text())

    def save(self) -> None:
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Title is required")
            return
        try:
            price = float(self.price_input.text()) if self.price_input.text() else 0.0
            stock = int(self.stock_input.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Invalid numbers", "Please check price and stock.")
            return
        description = self.description_input.toPlainText()
        category = self.category_input.text().strip()
        art_id_text = self.id_label.text()
        art_id = int(art_id_text) if art_id_text.isdigit() else None
        self.artworks.upsert_artwork(art_id, title, category, price, stock, description)
        self.refresh()

    def delete(self) -> None:
        art_id_text = self.id_label.text()
        if not art_id_text.isdigit():
            return
        self.artworks.delete_artwork(int(art_id_text))
        self.refresh()


class SettingsPage(QWidget):
    def __init__(self, settings: SettingsRepo):
        super().__init__()
        self.settings = settings
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Settings – Owner Profile"))
        form = QFormLayout()
        self.owner_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.alt_phone_input = QLineEdit()
        form.addRow("Owner Name", self.owner_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Alt Phone", self.alt_phone_input)
        layout.addLayout(form)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)
        self.setLayout(layout)
        self.refresh()

    def refresh(self) -> None:
        name, phone, alt = self.settings.get_settings()
        self.owner_input.setText(name)
        self.phone_input.setText(phone)
        self.alt_phone_input.setText(alt)

    def save(self) -> None:
        self.settings.update_settings(
            self.owner_input.text().strip(),
            self.phone_input.text().strip(),
            self.alt_phone_input.text().strip(),
        )
        QMessageBox.information(self, "Saved", "Contact details updated.")


class ReportsPage(QWidget):
    def __init__(self, orders: OrderRepo):
        super().__init__()
        self.orders = orders
        layout = QVBoxLayout()
        self.total_label = QLabel()
        self.pending_label = QLabel()
        self.revenue_label = QLabel()
        layout.addWidget(QLabel("Reports"))
        layout.addWidget(self.total_label)
        layout.addWidget(self.pending_label)
        layout.addWidget(self.revenue_label)
        self.setLayout(layout)
        self.refresh()

    def refresh(self) -> None:
        total, pending, revenue = self.orders.metrics()
        self.total_label.setText(f"Total orders: {total}")
        self.pending_label.setText(f"Pending COD: {pending}")
        self.revenue_label.setText(f"Revenue recorded: ₹{revenue:.0f}")


class AdminDashboardUI(QWidget):
    def __init__(self, db: DatabaseManager, notifications: NotificationManager):
        super().__init__()
        self.db = db
        self.notifications = notifications
        tabs = QTabWidget()
        self.dashboard = AdminDashboard(db.orders, notifications)
        self.history = OrdersHistory(db.orders)
        self.crud = ArtworkCrud(db.artworks)
        self.reports = ReportsPage(db.orders)
        self.settings = SettingsPage(db.settings)
        tabs.addTab(self.dashboard, "Dashboard")
        tabs.addTab(self.crud, "Products")
        tabs.addTab(self.history, "Orders")
        tabs.addTab(self.reports, "Reports")
        tabs.addTab(self.settings, "Settings")
        layout = QVBoxLayout()
        layout.addWidget(tabs)
        self.setLayout(layout)

    def refresh(self) -> None:
        self.dashboard.refresh()
        self.history.refresh()
        self.crud.refresh()
        self.reports.refresh()
        self.settings.refresh()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Art Hub – Desktop Ordering System")
        self.db = DatabaseManager()
        setattr(self.db.settings, "artwork_repo", self.db.artworks)
        self.notifications = NotificationManager()
        self.cart: Dict[int, int] = {}
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.logout_action = QAction("Logout", self)
        self.logout_action.triggered.connect(self.logout)
        self.logout_action.setEnabled(False)
        account_menu = self.menuBar().addMenu("Account")
        account_menu.addAction(self.logout_action)
        self.login = LoginUI(self.db.users)
        self.login.authenticated.connect(self.after_login)
        self.stack.addWidget(self.login)

        self.gallery = GalleryUI(self.db.artworks)
        self.gallery.add_to_cart.connect(self.add_artwork_to_cart)
        self.gallery.open_cart.connect(self.show_cart)
        self.stack.addWidget(self.gallery)

        self.admin_panel = AdminDashboardUI(self.db, self.notifications)
        self.stack.addWidget(self.admin_panel)

    def after_login(self, user: User) -> None:
        self.logout_action.setEnabled(True)
        if user.role.lower() == "admin":
            self.admin_panel.refresh()
            self.stack.setCurrentWidget(self.admin_panel)
        else:
            self.gallery.refresh()
            self.stack.setCurrentWidget(self.gallery)

    def logout(self) -> None:
        self.cart.clear()
        self.login.email_input.clear()
        self.login.password_input.clear()
        self.logout_action.setEnabled(False)
        self.gallery.update_cart_count(0)
        self.stack.setCurrentWidget(self.login)

    def add_artwork_to_cart(self, art_id: int, qty: int = 1) -> None:
        art = self.db.artworks.get_artwork(art_id)
        if not art:
            return
        current_qty = self.cart.get(art_id, 0)
        if art[4] < current_qty + qty:
            QMessageBox.information(self, "Stock", "No more stock available for this artwork.")
            return
        self.cart[art_id] = current_qty + qty
        QMessageBox.information(self, "Added", "Artwork added to cart.")
        self.gallery.update_cart_count(sum(self.cart.values()))

    def show_cart(self) -> None:
        dialog = CartDialog(self.db.artworks, self.cart, self)
        dialog.checkout_requested.connect(self.show_checkout)
        dialog.exec_()
        self.gallery.update_cart_count(sum(self.cart.values()))

    def show_checkout(self) -> None:
        checkout = CheckoutUI(self.db.orders, self.db.artworks, self.db.settings, self.cart, self)
        checkout.order_completed.connect(self._handle_order_complete)
        checkout.exec_()

    def _handle_order_complete(self, order_id: int) -> None:
        owner_name, owner_phone, alt_phone = self.db.settings.get_settings()
        order, lines = self.db.orders.get_order_details(order_id)
        item_summary = ", ".join([f"{t} x{q}" for t, q in lines])
        self.notifications.push_new_order(order_id, order[1], order[2], order[3], item_summary)
        contact = ContactDialogUI(owner_name, owner_phone, alt_phone, self)
        contact.exec_()
        confirmation = OrderConfirmationDialog(order[0], owner_phone, self)
        confirmation.exec_()
        self.cart.clear()
        self.gallery.refresh()
        self.gallery.update_cart_count(0)
        self.admin_panel.refresh()


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(960, 640)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

