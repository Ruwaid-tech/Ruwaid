# Storage Access Management Web App (MVP)

A complete Flask + SQLite MVP for private storage access control, with registration/login, email confirmation, admin approval, time-window access checks, and full audit logging.

## Stack
- Python + Flask
- SQLite + SQLAlchemy ORM
- Flask-Login (session auth)
- Flask-WTF (CSRF-protected forms)
- HTML/CSS/JavaScript (Jinja templates)

## One-command local run
```bash
./run.sh
```
Then open `http://127.0.0.1:5000` in a modern desktop browser.

## Manual setup (alternative)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## First admin bootstrap
Create the first admin account in another terminal:
```bash
source .venv/bin/activate
flask --app run.py seed-admin
```
Optional environment variables:
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

## Email confirmation in development
When a user registers, a confirmation link is generated and:
1. Logged to the Flask console (`Email confirmation link for ...`).
2. Shown in a flash message (`Dev confirmation link: ...`).

Clicking `/confirm/<token>` confirms email. The account still remains `INACTIVE` until admin approval.

## Security controls
- Password and PIN are hashed with Werkzeug.
- PIN verification runs exclusively server-side.
- SQLAlchemy ORM is used for parameterized database access.
- CSRF protection is enabled for forms.
- Admin routes use role + temporary role expiry checks (`role_expires_at`).
- Failed PIN attempts are tracked and every attempt is logged.
- Safe error pages are returned for 403/404/500.

## HTTPS requirement
Local development uses HTTP. Production **must** enforce HTTPS/TLS termination (reverse proxy or platform TLS), set secure cookies, and preferably HSTS.

## Run tests
```bash
pytest
```
