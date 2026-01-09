import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DB_MODE = os.getenv("PAWLOG_DB_MODE", "sqlite").lower()

MYSQL_CONFIG = {
    "host": os.getenv("PAWLOG_MYSQL_HOST", "localhost"),
    "port": int(os.getenv("PAWLOG_MYSQL_PORT", "3306")),
    "user": os.getenv("PAWLOG_MYSQL_USER", "root"),
    "password": os.getenv("PAWLOG_MYSQL_PASSWORD", ""),
    "database": os.getenv("PAWLOG_MYSQL_DB", "pawlog"),
}

SQLITE_PATH = os.getenv("PAWLOG_SQLITE_PATH", str(BASE_DIR / "db" / "pawlog.db"))

AUTO_LOGOUT_MINUTES = int(os.getenv("PAWLOG_AUTO_LOGOUT_MINUTES", "10"))

APP_TITLE = "Pawlog"
