from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .forms import LoginForm, RegisterForm
from .models import User, UserStatus
from .security import confirm_token, generate_confirmation_token


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            password_hash=generate_password_hash(form.password.data),
            status=UserStatus.INACTIVE,
        )
        db.session.add(user)
        db.session.commit()

        token = generate_confirmation_token(current_app, user.email)
        confirm_link = url_for("auth.confirm_email", token=token, _external=True)
        current_app.logger.info("Email confirmation link for %s: %s", user.email, confirm_link)
        flash("Registration successful. Confirm your email from the dev console link, then wait for admin approval.", "info")
        flash(f"Dev confirmation link: {confirm_link}", "warning")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = confirm_token(current_app, token)
    except Exception:
        flash("Confirmation link is invalid or expired.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    if user.email_confirmed:
        flash("Email already confirmed. Await admin approval.", "info")
        return redirect(url_for("auth.login"))

    user.email_confirmed_at = datetime.utcnow()
    db.session.commit()
    flash("Email confirmed. Your account remains inactive until admin approval.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if not user or not check_password_hash(user.password_hash, form.password.data):
            flash("Invalid credentials.", "danger")
            return render_template("login.html", form=form)

        if not user.email_confirmed:
            flash("Please confirm your email first.", "warning")
            return render_template("login.html", form=form)

        login_user(user)
        return redirect(url_for("main.dashboard"))

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
