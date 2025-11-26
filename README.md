# ART HUB – Flask Web App

A minimal Flask + SQLite implementation of the ART HUB wireframes. Buyers browse the gallery, add to cart, and place Cash-on-Delivery orders. Admins manage orders, artworks, and owner contact details.

## Setup
```bash
pip install flask werkzeug
python db_init.py
python app.py
```

Admin login seeded via `db_init.py`:
- Username: `admin`
- Password: `admin123`

## Structure
- `app.py` – Flask routes and business logic
- `db_init.py` – Recreate and seed the database
- `templates/` – Jinja2 templates for public and admin views
- `static/` – CSS/JS assets

## Notes
- Orders generate codes like `ORD-YYYY-00001`
- Checkout is COD-only and shows owner contact info after submission
