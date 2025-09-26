# Kitchen Manager Application

This repository contains a **Python + SQLite** desktop application designed to
support the workflow of a medium-sized restaurant kitchen.  The solution is
implemented entirely with Tkinter and follows the success criteria agreed with
the client: secure user access, inventory monitoring with low-stock alerts,
recipe management tied to inventory usage, a real-time cooking checklist and
report generation.

## Features

* **Authentication** – Users can register and log in using hashed passwords.
* **Dashboard** – Provides quick navigation to inventory, recipe and report
  modules along with a personalised greeting.
* **Inventory Management** – Add, update or delete items with automatic unit
  conversions (g/kg, ml/l, unit).  Low stock levels trigger in-app alerts.
* **Recipe Management** – Store multi-step recipes, assign ingredients sourced
  from the inventory and initiate the cooking workflow.
* **Cooking Checklist** – A step-by-step checklist opens when cooking starts.
  Ingredients are deducted from the inventory immediately and a completion
  confirmation is displayed after all steps are ticked.
* **Reports** – View recipe popularity, ingredient consumption totals and a
  consolidated low-stock list to inform restocking decisions.

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
* Reports are recalculated every time the **Reports** page is opened, so
  cooking new dishes immediately updates the analytics.

## Screenshots

The GUI is responsive to window resizing.  For assessment submissions, capture
screenshots directly from the running Tkinter window that demonstrate the main
workflows (login, inventory, recipes, checklist and reports).

