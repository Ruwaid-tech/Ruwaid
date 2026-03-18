from flask import current_app, url_for

from .email_service import EmailService


def send_confirmation_email(user_email: str, token: str) -> None:
    confirm_link = url_for("confirm_email", token=token, _external=True)
    text_body = (
        "Welcome to Storage Access Manager.\n\n"
        "Please confirm your email address by opening this link:\n"
        f"{confirm_link}\n\n"
        "Your account will stay inactive until an administrator approves it."
    )
    html_body = (
        "<p>Welcome to <strong>Storage Access Manager</strong>.</p>"
        f"<p>Please <a href=\"{confirm_link}\">confirm your email address</a>.</p>"
        "<p>Your account will remain inactive until an administrator approves it.</p>"
    )
    EmailService(current_app).send_email(
        to_email=user_email,
        subject="Confirm your Storage Access Manager account",
        text_body=text_body,
        html_body=html_body,
    )



def send_pin_assignment_email(user_email: str, pin_code: str) -> None:
    text_body = (
        "Your Storage Access Manager account has been approved.\n\n"
        f"Your PIN code is: {pin_code}\n\n"
        "Keep this PIN secure. Enter it in the web app when attempting access."
    )
    html_body = (
        "<p>Your <strong>Storage Access Manager</strong> account has been approved.</p>"
        f"<p><strong>Your PIN code is: {pin_code}</strong></p>"
        "<p>Keep this PIN secure and use it in the web app when attempting access.</p>"
    )
    EmailService(current_app).send_email(
        to_email=user_email,
        subject="Your Storage Access Manager PIN code",
        text_body=text_body,
        html_body=html_body,
    )
