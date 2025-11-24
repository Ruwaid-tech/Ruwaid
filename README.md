# Art Hub Desktop (PyQt + SQLite)

A standalone, offline-friendly desktop application for Ms. Priya Sharma to manage artwork browsing and Cash-on-Delivery orders. The app follows the provided IA wireframes and diagrams: buyers can explore a gallery, view details, add items to a cart, and confirm COD checkout that immediately shows the owner's contact. Admins receive notifications for every order, manage artwork inventory through CRUD, and update the contact profile stored in SQLite.

## Features aligned to success criteria
- **Gallery with stock-aware cards (SC1):** Search, category and sort controls feed a table of artworks with live stock counts. Disabled “Add to cart” buttons prevent overselling.
- **Checkout with validation (SC2):** Buyers enter name, phone, and address; orders are rejected if fields are missing or stock is insufficient.
- **Contact Owner dialog (SC3 & SC7):** After confirming an order, a modal displays the latest owner name and phone from the `settings` table.
- **Admin notifications (SC4):** The dashboard lists every order with buyer details, items, status, and timestamps, with a quick “Mark Contacted” action.
- **Artwork CRUD (SC5):** Admins can add, edit, and delete artworks, updating both the UI and database.
- **SQLite persistence (SC6):** Orders, order lines, users, settings, and artworks are stored in `art_hub.db`.

## Project layout
- `app.py` – Main PyQt5 application, UI flows, and SQLite data layer.
- `art_hub.db` – Created on first run with seeded users, owner profile, and 10 sample artworks.
- `requirements.txt` – Python dependencies (PyQt5).

Legacy static site files (`index.html`, `routes.html`, `reflections.html`, `css/`, `js/`, `img/`, `data/`) remain untouched and can be ignored for the desktop app.

## Getting started
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the desktop app**
   ```bash
   python app.py
   ```
   The first launch seeds the database with:
   - Admin: `admin@arthub.com` / `admin123`
   - Buyer: `buyer@arthub.com` / `buyer123`
   - Or create a new buyer account directly from the login screen.
3. **Buyer flow**
   - Log in as the buyer, search/filter the gallery, add items to the cart, and open Checkout.
   - Confirm COD: the order is saved, the Contact Owner dialog appears, and a confirmation summary displays the next action.
4. **Admin flow**
   - Log in as the admin to view new-order notifications, mark them contacted, manage artworks via CRUD, and edit owner contact info.
   - Updating owner details instantly changes what buyers see in the Contact Owner dialog.

## Database schema (SQLite)
- **users**: `id`, `email` (unique), `password_hash`, `role` (`admin`/`buyer`), `name`
- **artworks**: `id`, `title`, `category`, `price`, `image_path`, `stock`, `description`
- **orders**: `id`, `buyer_name`, `phone`, `address`, `status`, `created_at`
- **order_lines**: `id`, `order_id` → `orders.id`, `artwork_id` → `artworks.id`, `qty`, `unit_price`
- **settings**: `id` (singleton row), `owner_name`, `owner_phone`

## Notes for Criterion D testing
- Inserted seed data includes 10 artworks; use admin CRUD to adjust or add more.
- Order placement decreases stock and populates both `orders` and `order_lines` for verification in any SQLite viewer.
- Change owner contact in Settings, then place another order to verify the Contact Owner dialog updates automatically.
