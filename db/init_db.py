from db.db import db


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pets (
    pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    breed TEXT NOT NULL,
    coat_color TEXT NOT NULL,
    eye_color TEXT NOT NULL,
    owner_phone TEXT NOT NULL,
    photo_path TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feeding_logs (
    feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER NOT NULL,
    scheduled_datetime TEXT NOT NULL,
    food_type TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    completed_at TEXT,
    completed_by INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY(pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE,
    FOREIGN KEY(completed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS health_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('vet','vaccination','medication','exercise')),
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    notes TEXT,
    dosage TEXT,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS weight_logs (
    weight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    weight_kg REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schedules (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('medication','vaccination','vet')),
    title TEXT NOT NULL,
    due_datetime TEXT NOT NULL,
    repeat_rule TEXT,
    status TEXT NOT NULL DEFAULT 'due' CHECK (status IN ('due','done','snoozed')),
    snoozed_until TEXT,
    done_at TEXT,
    done_by INTEGER,
    FOREIGN KEY(pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE,
    FOREIGN KEY(done_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
"""

MYSQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS pets (
    pet_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    breed VARCHAR(100) NOT NULL,
    coat_color VARCHAR(50) NOT NULL,
    eye_color VARCHAR(50) NOT NULL,
    owner_phone VARCHAR(30) NOT NULL,
    photo_path VARCHAR(255),
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS feeding_logs (
    feed_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT NOT NULL,
    scheduled_datetime DATETIME NOT NULL,
    food_type VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    unit VARCHAR(10) NOT NULL,
    completed_at DATETIME NULL,
    completed_by INT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE,
    FOREIGN KEY (completed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS health_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT NOT NULL,
    type ENUM('vet','vaccination','medication','exercise') NOT NULL,
    date DATE NOT NULL,
    title VARCHAR(100) NOT NULL,
    notes TEXT,
    dosage VARCHAR(100),
    created_by INT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS weight_logs (
    weight_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT NOT NULL,
    date DATE NOT NULL,
    weight_kg DECIMAL(6,2) NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT NOT NULL,
    event_type ENUM('medication','vaccination','vet') NOT NULL,
    title VARCHAR(100) NOT NULL,
    due_datetime DATETIME NOT NULL,
    repeat_rule VARCHAR(50),
    status ENUM('due','done','snoozed') NOT NULL DEFAULT 'due',
    snoozed_until DATETIME NULL,
    done_at DATETIME NULL,
    done_by INT NULL,
    FOREIGN KEY (pet_id) REFERENCES pets(pet_id) ON DELETE CASCADE,
    FOREIGN KEY (done_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""


def init_db() -> None:
    schema = MYSQL_SCHEMA if db.mode == "mysql" else SQLITE_SCHEMA
    statements = [stmt.strip() for stmt in schema.split(";") if stmt.strip()]
    for stmt in statements:
        db.execute(stmt)


if __name__ == "__main__":
    init_db()
