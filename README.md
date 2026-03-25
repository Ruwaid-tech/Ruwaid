# Painting Tracker

Painting Tracker is a desktop application built for **Sharmila Vijay Moorthy** to manage painting projects, future ideas, completed artworks, and art materials in one simple tool.

## Tech Stack
- Python 3
- Tkinter (`tkinter` + `ttk`) for GUI
- SQLite3 for local persistent storage

## File Structure
- `app.py` — Main Tkinter application with all screens, navigation, forms, and CRUD actions.
- `database.py` — SQLite database initialization and data access methods.
- `painting_tracker.db` — Automatically created after first run.

## How to Run
1. Make sure Python 3 is installed.
2. Run the app from the project folder:
   ```bash
   python app.py
   ```
3. Login with default credentials (created automatically when DB is empty):
   - **Username:** `admin`
   - **Password:** `admin123`

## Features Included
- Secure login validation
- Dashboard navigation
- Current projects management (add/edit/delete/view)
- Future ideas management (add/edit/delete/view)
- Materials/equipment management (add/edit/delete/view)
- Previous projects/gallery list with details popup
- Image path support with file picker
- Settings screen with password change
- SQLite persistence across app restarts
