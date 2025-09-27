# Kitchen Manager Application

This repository contains a **Python + SQLite** desktop application designed to
support the workflow of a medium-sized restaurant kitchen.  The solution is
implemented entirely with Tkinter and follows the success criteria agreed with
the client: secure user access, inventory monitoring with low-stock alerts,
recipe management tied to inventory usage, a real-time cooking checklist and
report generation.

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
  consolidated low-stock list to inform restocking decisions.
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

The first launch creates `kitchen_manager.db` in the repository root.  Use the
“Register” button to create an account before logging in.

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

