from datetime import datetime
from functools import wraps

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .forms import AccessWindowForm, LogFilterForm, LoginForm, PinAttemptForm, RegisterForm, TempAdminForm
from .models import AccessLog, AccessResult, AccessWindow, User, UserRole, UserStatus
from .security import confirm_token, generate_confirmation_token, generate_unique_pin, hash_pin, process_access_attempt


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_admin_access():
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def register_routes(app):
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            existing = User.query.filter_by(email=form.email.data.lower().strip()).first()
            if existing:
                flash("Email already registered.", "error")
            else:
                user = User(
                    email=form.email.data.lower().strip(),
                    password_hash=generate_password_hash(form.password.data),
                    status=UserStatus.INACTIVE,
                    role=UserRole.USER,
                )
                db.session.add(user)
                db.session.commit()
                token = generate_confirmation_token(app, user.email)
                confirm_link = url_for("confirm_email", token=token, _external=True)
                app.logger.info("Email confirmation link for %s: %s", user.email, confirm_link)
                flash("Registration successful. Check your email to confirm your account.", "success")
                flash(f"Dev confirmation link: {confirm_link}", "info")
                return redirect(url_for("login"))
        return render_template("register.html", form=form)

    @app.route("/confirm/<token>")
    def confirm_email(token):
        try:
            email = confirm_token(app, token)
        except Exception:
            flash("Invalid or expired confirmation link.", "error")
            return redirect(url_for("login"))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.", "error")
        elif user.email_confirmed:
            flash("Email already confirmed.", "info")
        else:
            user.email_confirmed_at = datetime.utcnow()
            db.session.commit()
            flash("Email confirmed. Await admin approval to activate account.", "success")
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower().strip()).first()
            if not user or not check_password_hash(user.password_hash, form.password.data):
                flash("Invalid credentials.", "error")
                return render_template("login.html", form=form)
            if not user.email_confirmed:
                flash("Please confirm your email before logging in.", "error")
                return render_template("login.html", form=form)
            login_user(user)
            return redirect(url_for("dashboard"))
        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard", methods=["GET", "POST"])
    @login_required
    def dashboard():
        if current_user.has_admin_access():
            return redirect(url_for("admin_dashboard"))

        pin_form = PinAttemptForm()
        result_msg = None
        if pin_form.validate_on_submit():
            allowed, message = process_access_attempt(
                current_user.user_id,
                pin_form.entered_code.data,
                datetime.utcnow(),
                request.remote_addr,
            )
            result_msg = f"{('GRANT' if allowed else 'DENY')}: {message}"

        active_window = AccessWindow.query.filter_by(user_id=current_user.user_id).order_by(AccessWindow.end_time.desc()).first()
        return render_template("user_dashboard.html", pin_form=pin_form, result_msg=result_msg, window=active_window)

    @app.route("/my-history")
    @login_required
    def my_history():
        logs = AccessLog.query.filter_by(user_id=current_user.user_id).order_by(AccessLog.timestamp.desc()).all()
        return render_template("my_history.html", logs=logs)

    @app.route("/user/<int:user_id>/history")
    @login_required
    def user_history(user_id):
        if current_user.user_id != user_id and not current_user.has_admin_access():
            abort(403)
        logs = AccessLog.query.filter_by(user_id=user_id).order_by(AccessLog.timestamp.desc()).all()
        return render_template("my_history.html", logs=logs)

    @app.route("/admin/dashboard")
    @login_required
    @admin_required
    def admin_dashboard():
        pending_count = User.query.filter_by(status=UserStatus.INACTIVE).count()
        recent_attempts = AccessLog.query.filter(AccessLog.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).count()
        return render_template("admin_dashboard.html", pending_count=pending_count, recent_attempts=recent_attempts)

    @app.route("/admin/users", methods=["GET", "POST"])
    @login_required
    @admin_required
    def manage_users():
        temp_admin_form = TempAdminForm()
        users = User.query.order_by(User.created_at.desc()).all()
        return render_template("manage_users.html", users=users, temp_admin_form=temp_admin_form)

    @app.route("/admin/users/<int:user_id>/approve", methods=["POST"])
    @login_required
    @admin_required
    def approve_user(user_id):
        user = User.query.get_or_404(user_id)
        if not user.email_confirmed:
            flash("User must confirm email first.", "error")
            return redirect(url_for("manage_users"))

        pin = generate_unique_pin()
        user.pin_hash = hash_pin(pin)
        user.status = UserStatus.ACTIVE
        user.failed_pin_attempts = 0
        user.last_failed_at = None
        db.session.commit()
        flash(f"User {user.email} approved. Temporary PIN shown once: {pin}", "success")
        return redirect(url_for("manage_users"))

    @app.route("/admin/users/<int:user_id>/deactivate", methods=["POST"])
    @login_required
    @admin_required
    def deactivate_user(user_id):
        user = User.query.get_or_404(user_id)
        user.status = UserStatus.INACTIVE
        db.session.commit()
        flash(f"User {user.email} deactivated.", "info")
        return redirect(url_for("manage_users"))

    @app.route("/admin/users/<int:user_id>/temp-admin", methods=["POST"])
    @login_required
    @admin_required
    def set_temp_admin(user_id):
        form = TempAdminForm()
        if form.validate_on_submit():
            user = User.query.get_or_404(user_id)
            user.role = UserRole.ADMIN
            user.role_expires_at = form.role_expires_at.data
            db.session.commit()
            flash(f"Temporary admin access granted to {user.email}", "success")
        else:
            flash("Invalid expiration date.", "error")
        return redirect(url_for("manage_users"))

    @app.route("/admin/users/<int:user_id>/clear-admin", methods=["POST"])
    @login_required
    @admin_required
    def clear_temp_admin(user_id):
        user = User.query.get_or_404(user_id)
        user.role = UserRole.USER
        user.role_expires_at = None
        db.session.commit()
        flash(f"Admin access removed from {user.email}", "info")
        return redirect(url_for("manage_users"))

    @app.route("/admin/windows", methods=["GET", "POST"])
    @login_required
    @admin_required
    def set_access_windows():
        form = AccessWindowForm()
        form.user_id.choices = [(u.user_id, f"{u.email} (#{u.user_id})") for u in User.query.order_by(User.email.asc()).all()]

        if form.validate_on_submit():
            AccessWindow.query.filter_by(user_id=form.user_id.data).delete()
            window = AccessWindow(user_id=form.user_id.data, start_time=form.start_time.data, end_time=form.end_time.data)
            db.session.add(window)
            db.session.commit()
            flash("Access window updated.", "success")
            return redirect(url_for("set_access_windows"))

        windows = AccessWindow.query.order_by(AccessWindow.start_time.desc()).all()
        return render_template("set_windows.html", form=form, windows=windows)

    @app.route("/admin/logs", methods=["GET", "POST"])
    @login_required
    @admin_required
    def view_logs():
        form = LogFilterForm(request.form)
        query = AccessLog.query

        if form.validate_on_submit():
            if form.user_id.data and form.user_id.data.isdigit():
                query = query.filter(AccessLog.user_id == int(form.user_id.data))
            if form.result.data:
                query = query.filter(AccessLog.result == AccessResult(form.result.data))
            if form.start_time.data:
                query = query.filter(AccessLog.timestamp >= form.start_time.data)
            if form.end_time.data:
                query = query.filter(AccessLog.timestamp <= form.end_time.data)

        logs = query.order_by(AccessLog.timestamp.desc()).limit(500).all()
        return render_template("admin_logs.html", logs=logs, form=form)
