# Art Hub – Desktop Ordering System

A fully offline PyQt5 + SQLite desktop app that mirrors the provided ASCII wireframes for ART HUB. Buyers browse a gallery, view artwork details, add items to a cart, and complete a Cash-on-Delivery checkout that immediately shows the owner contact dialog. Admins see new-order notifications, manage inventory with CRUD, update the owner profile, and review reports.

## Features aligned to success criteria
- **SC1: Gallery with 10+ artworks** – Seeded catalogue with search, category filter, and price sort using card-style listings with View/Add buttons.
- **SC2: COD order creation** – Checkout enforces required name/phone/address with E.164 validation and stock checks before inserting `orders` and `order_lines`.
- **SC3 & SC7: Contact Owner dialog** – Pulls live owner info from the `settings` table after every order; editing Settings updates the dialog instantly.
- **SC4: Admin notifications** – Orders set to `Pending COD` automatically surface in the dashboard notification panel with quick actions.
- **SC5: Artwork CRUD** – Admin Products tab supports add/edit/delete with live refresh of gallery categories.
- **SC6: Accurate order storage** – Orders and order lines are stored with stock decremented accordingly and shown in Order History and Reports.

## Project layout
- `app.py` – All UI flows (LoginUI, GalleryUI, DetailUI, CheckoutUI, ContactDialogUI, AdminDashboardUI) plus repositories (`UserRepo`, `ArtworkRepo`, `OrderRepo`, `SettingsRepo`) and `NotificationManager`.
- `main.py` – Entry point that launches the PyQt application.
- `init_db.py` – Initializes and seeds the SQLite database without opening the UI.
- `art_hub.db` – Created/seeded on first run with admin + buyer accounts, owner profile, and 10 sample artworks.
- `images/` – Placeholder directory for artwork thumbnails. Files are generated at runtime from embedded base64, so no binary assets are tracked in git.
- `requirements.txt` – Python dependency list.

## Getting started
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Initialize the database (optional)**
   ```bash
   python init_db.py
   ```
3. **Run the desktop app**
   ```bash
   python main.py
   ```
   Default accounts:
   - Admin: `admin@arthub.com` / `admin123`
   - Buyer: `buyer@arthub.com` / `buyer123`

## Buyer flow
- Log in as a buyer, filter/sort the gallery, view details (with qty selector), and add items to the cart.
- Open Checkout → validate fields → create order (status `Pending COD`) → Contact Owner dialog → order confirmation card.

## Admin flow
- Log in as admin to see Dashboard notifications (⚠ NEW ORDER) with Call/Mark Contacted/View actions.
- Manage inventory in **Products**, review **Orders** history, see **Reports** totals, and edit **Settings** (owner/phone).

## Database schema (SQLite)
- **users**: `id`, `email` (unique), `password_hash`, `role` (`admin`/`buyer`), `name`
- **artworks**: `id`, `title`, `category`, `price`, `image_path`, `stock`, `description`
- **orders**: `id`, `buyer_name`, `phone`, `address`, `status`, `created_at`
- **order_lines**: `id`, `order_id` → `orders.id`, `artwork_id` → `artworks.id`, `qty`, `unit_price`
- **settings**: `id` (singleton row), `owner_name`, `owner_phone`, `alt_phone`

## Notes
- The UI intentionally mirrors the ASCII wireframes: Courier-like typography, bordered cards, and icon headers (✓, ⚠, 🎉).
- The COD-only workflow implements the provided flowchart and UML sequence: validate → save order → fetch owner info → show contact dialog → notify admin → show confirmation.
