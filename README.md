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

## Email delivery
The app now includes actual email-delivery handling instead of only showing links in flash messages.

### Development mode
By default, emails are written to `instance/dev_mailbox.json` and also logged to the console. You can inspect them in either of these ways:
1. Open the **Dev Mailbox** page in the web UI.
2. Read the JSON outbox file on disk.

This includes:
- registration confirmation emails containing the `/confirm/<token>` link;
- approval emails containing the one-time generated PIN code.

### SMTP mode
You can switch to real SMTP delivery by overriding config values such as:
- `MAIL_DELIVERY=smtp`
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USE_TLS`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`

If SMTP delivery fails, the app returns a safe message and logs the delivery failure server-side.

## Approval and PIN flow
1. A user registers.
2. The system sends a confirmation email.
3. The user confirms their email address.
4. The account remains `INACTIVE` until an admin approves it.
5. On approval, the system generates a unique PIN, stores only the PIN hash, and emails the plaintext PIN to the user.

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
