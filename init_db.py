"""Initialize the Art Hub SQLite database with seed data."""
from app import DatabaseManager


def main() -> None:
    DatabaseManager()
    print("Database initialized and seeded at art_hub.db")


if __name__ == "__main__":
    main()
