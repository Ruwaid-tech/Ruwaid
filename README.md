# Pawlog Desktop App

Pawlog is a cross-platform desktop app for tracking foster/recovery pets, feeding logs, health records, and reminders.

## Features
- Secure login with bcrypt password hashing
- Pet profiles with photo upload
- Feeding logs with completion checklist
- Health records and schedules (vaccinations, meds, vet visits, exercise)
- Notifications with snooze and completion
- Health score analytics with Matplotlib charts
- MySQL preferred, SQLite fallback (same schema)

## Setup

### 1) Install Python 3.11+

### 2) Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) Database configuration
By default the app uses SQLite at `db/pawlog.db`.

To use MySQL, set environment variables:
```bash
export PAWLOG_DB_MODE=mysql
export PAWLOG_MYSQL_HOST=localhost
export PAWLOG_MYSQL_PORT=3306
export PAWLOG_MYSQL_USER=root
export PAWLOG_MYSQL_PASSWORD=yourpassword
export PAWLOG_MYSQL_DB=pawlog
```

### 4) Initialize DB + seed data
```bash
python seed.py
```
This creates an admin user: `admin / password123` and sample data.

### 5) Run the app
```bash
python main.py
```

## Notes
- All database queries use parameterized statements.
- Auto-logout is enabled after 10 minutes of inactivity.
- Email alerts are stubbed; app alerts are in-app reminders.
