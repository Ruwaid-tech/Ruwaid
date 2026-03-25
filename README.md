# Kitchen Manager Application

This repository contains a **Python + SQLite** desktop application designed to
support the workflow of a medium-sized restaurant kitchen.  The solution is
implemented entirely with Tkinter and follows the success criteria agreed with
the client: secure user access, inventory monitoring with low-stock alerts,
recipe management tied to inventory usage, a real-time cooking checklist and
report generation.

## Product overview

Kitchen Manager is a desktop operations app for restaurant kitchens. It helps
staff replace paper logs, ad-hoc spreadsheets and chat-based ordering with one
central system that handles:

* secure logins for kitchen users
* ingredient stock tracking and low-stock warnings
* supplier records and vendor purchasing workflows
* recipe storage with step-by-step cooking support
* customer order progress tracking
* reporting on dish volume, ingredient usage and reorder needs

The goal is to make kitchen decisions faster and more accurate during rush
hours by keeping all operational data in one place.

## What is used (technology stack)

### Core technologies

* **Python 3** – Application logic, UI event handling and data operations.
* **SQLite (`sqlite3`)** – Embedded relational database for persistent storage.
* **Tkinter + `ttk`** – Native desktop GUI framework for all screens.

### Python standard-library modules used in this project

* **`tkinter` / `tkinter.ttk` / `tkinter.messagebox`** – widgets, themed
  controls and dialogs.
* **`tkinter.font`** – cross-platform font handling for stable UI rendering.
* **`sqlite3`** – SQL execution, schema setup and transactions.
* **`datetime`** – timestamps for orders, sessions and reporting periods.
* **`dataclasses`** – lightweight typed records for supplier/order entities.
* **`typing`** – type hints for maintainability and clearer interfaces.
* **`contextlib` / `pathlib`** – safer DB resource handling and file paths.

### Data model areas in SQLite

* users and credentials
* inventory items and thresholds
* recipes, recipe ingredients and recipe steps
* cooking sessions/completions
* suppliers and vendor orders
* customer orders
* application settings and theme preferences

## Features

* **Authentication** – Users can register and log in securely from the desktop client.
* **Dashboard** – Presents shortcuts to every workflow (inventory, rapid stock
  edits, suppliers, vendor orders, recipes, customer orders, reports and
  settings) while surfacing pending orders and low stock counts.
* **Inventory Management** – Add, update or delete items with automatic unit
  conversions (g/kg, ml/l, unit/dozen).  Low stock levels trigger in-app alerts.
* **Edit Inventory workspace** – Quickly adjust quantities or thresholds for
  existing stock items without re-entering their metadata.
* **Supplier directory** – Maintain vendor contact information and notes so
  purchase orders can be raised against the correct partner.
* **Vendor Orders** – Log purchase orders, track their status and automatically
  restock inventory when deliveries are marked as received.
* **Recipe Management** – Store multi-step recipes, assign ingredients sourced
  from the inventory and initiate the cooking workflow.
* **Cooking Checklist** – A step-by-step checklist opens when cooking starts.
  Ingredients are deducted from the inventory immediately and a completion
  confirmation is displayed after all steps are ticked.
* **Customer Orders** – Capture dine-in demand, progress orders through their
  lifecycle and deduct inventory when meals are marked as completed.
* **Reports** – View recipe popularity, ingredient consumption totals and a
  consolidated low-stock list to inform restocking decisions.  Embedded bar
  charts highlight the top-performing dishes and most-used ingredients.
* **Theme toggle** – Switch between coordinated light and dark palettes without
  restarting the program; the preference is saved per user profile.
* **Settings** – Store branded preferences such as restaurant name, default
  vendor lead times and notification contact details.

## Project structure

```
.
├── app.py            # Tkinter user interface
├── database.py       # SQLite schema + data access helpers
└── kitchen_manager.db (created on first run)
```

## Getting started

1. Ensure Python 3.10+ is installed.
2. Install optional dependencies (Tkinter ships with the standard library on
   most platforms; on Linux you may need the `python3-tk` package).
3. Run the application:

   ```bash
   python app.py
   ```

The first launch creates `kitchen_manager.db` in the repository root.  A sample
`manager` account with password `kitchen123` is preloaded, along with inventory,
suppliers, vendor orders, recipes, cooking history and customer orders so you
can demo the workflows immediately.  You can also use the “Register” button to
add additional accounts.

## Usage tips

* Quantities can be entered in grams/millilitres or kilograms/litres.  The
  system automatically normalises values and displays them in the most
  appropriate unit.
* Recipes cannot be cooked until all required ingredients exist in the
  inventory with sufficient stock.  The application will list shortages.
* Supplier and vendor order directories power the automatic restocking flow –
  once a delivery is marked **Received**, the inventory updates instantly.
* Customer orders can be marked **In Progress** or **Completed** to mirror the
  kitchen workflow and keep ingredient usage analytics accurate.
* Reports are recalculated every time the **Reports** page is opened, so
  cooking new dishes immediately updates the analytics.

## Screenshots

The GUI is responsive to window resizing.  For assessment submissions, capture
screenshots directly from the running Tkinter window that demonstrate the main
workflows (login, inventory, recipes, checklist and reports).
