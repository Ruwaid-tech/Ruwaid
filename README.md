# Storage Access Management Web App (MVP)

Flask + SQLite MVP for private storage access control.

## Features
- Registration/login with email confirmation token flow.
- New users default to `INACTIVE` and require admin approval.
- Admin approval activates user and generates unique PIN (stored hashed only).
- Server-side PIN validation through `process_access_attempt`.
- Access windows support (`start_time` / `end_time`) with deny when outside window.
- All access attempts are logged (grant/deny, reason, timestamp, user_id nullable, IP).
- RBAC-protected admin pages.
- Users can only view their own history.
- Temporary admin roles via `role_expires_at`.
- Failed PIN counters (`failed_pin_attempts`, `last_failed_at`) and per-attempt logs.

## Quick Start
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python app.py
```
Open `http://127.0.0.1:5000`.

## Admin bootstrap
Create first admin:
```bash
flask --app app seed-admin
```
Optional env vars:
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

## Email confirmation in development
During registration, confirmation link is:
1. Logged to Flask console (`Email confirmation link for ...`).
2. Shown as a flash message (`Dev confirmation link: ...`).

Click the link to mark email confirmed. Account remains inactive until admin approval.

## Security notes
- Password + PIN are hashed with Werkzeug.
- SQLAlchemy ORM parameterization used for DB access.
- CSRF enabled with Flask-WTF forms.
- Admin routes gated by role + `role_expires_at`.
- Error handlers return safe messages instead of raw stack traces.

## HTTPS requirement
Local development uses HTTP. **Production deployment must terminate TLS and enforce HTTPS** (e.g., Nginx/Traefik reverse proxy + HSTS), and secure cookies should be enabled.

## Test
```bash
pytest
```
