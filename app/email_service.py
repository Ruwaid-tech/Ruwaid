from __future__ import annotations

import json
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from flask import current_app


class EmailDeliveryError(RuntimeError):
    """Raised when an email cannot be delivered."""


class DevMailbox:
    def __init__(self, outbox_path: str | Path):
        self.outbox_path = Path(outbox_path)
        self.outbox_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.outbox_path.exists():
            self.outbox_path.write_text("[]", encoding="utf-8")

    def load_messages(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.outbox_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def append_message(self, payload: dict[str, Any]) -> None:
        messages = self.load_messages()
        messages.insert(0, payload)
        self.outbox_path.write_text(json.dumps(messages, indent=2), encoding="utf-8")


class EmailService:
    def __init__(self, app=None):
        self.app = app

    def init_app(self, app):
        self.app = app

    def send_email(self, *, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        app = self.app or current_app
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = app.config["MAIL_DEFAULT_SENDER"]
        message["To"] = to_email
        message.set_content(text_body)
        if html_body:
            message.add_alternative(html_body, subtype="html")

        payload = {
            "to": to_email,
            "from": app.config["MAIL_DEFAULT_SENDER"],
            "subject": subject,
            "text_body": text_body,
            "html_body": html_body,
            "sent_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

        delivery_mode = app.config.get("MAIL_DELIVERY", "console_and_file")
        if delivery_mode == "smtp":
            self._send_via_smtp(app, message)
        elif delivery_mode == "console_and_file":
            app.logger.info("Sending email to %s with subject %s", to_email, subject)
        else:
            raise EmailDeliveryError(f"Unsupported mail delivery mode: {delivery_mode}")

        mailbox = DevMailbox(app.config["DEV_EMAIL_OUTBOX"])
        mailbox.append_message(payload)
        app.logger.info("Email stored in dev outbox for %s at %s", to_email, app.config["DEV_EMAIL_OUTBOX"])

    def _send_via_smtp(self, app, message: EmailMessage) -> None:
        try:
            with smtplib.SMTP(app.config["MAIL_SERVER"], app.config["MAIL_PORT"], timeout=10) as server:
                if app.config.get("MAIL_USE_TLS"):
                    server.starttls()
                username = app.config.get("MAIL_USERNAME")
                password = app.config.get("MAIL_PASSWORD")
                if username and password:
                    server.login(username, password)
                server.send_message(message)
        except OSError as exc:
            raise EmailDeliveryError("Failed to send email via SMTP.") from exc

    def list_messages(self) -> list[dict[str, Any]]:
        app = self.app or current_app
        mailbox = DevMailbox(app.config["DEV_EMAIL_OUTBOX"])
        return mailbox.load_messages()
