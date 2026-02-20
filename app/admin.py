from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .forms import AccessWindowForm, RoleExpiryForm
from .models import AccessLog, AccessResult, AccessWindow, User, UserRole, UserStatus
from .security import generate_pin, hash_pin


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    if not current_user.is_authenticated or not current_user.has_admin_access():
        abort(403)


@admin_bp.before_request
def enforce_admin():
    admin_required()


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    pending_count = User.query.filter_by(status=UserStatus.INACTIVE).count()
    recent_attempts = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(10).count()
    return render_template("admin_dashboard.html", pending_count=pending_count, recent_attempts=recent_attempts)


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    role_form = RoleExpiryForm(prefix="role")
    return render_template("manage_users.html", users=users, role_form=role_form)


@admin_bp.route("/users/<int:user_id>/approve", methods=["POST"])
@login_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.email_confirmed:
        flash("Cannot approve unconfirmed email.", "warning")
        return redirect(url_for("admin.manage_users"))

    user.status = UserStatus.ACTIVE
    raw_pin = generate_pin()
    user.pin_hash = hash_pin(raw_pin)
    db.session.commit()
    flash(f"User approved. Temporary PIN for {user.email}: {raw_pin}", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@login_required
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = UserStatus.INACTIVE
    db.session.commit()
    flash("User deactivated.", "info")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/<int:user_id>/set-temp-admin", methods=["POST"])
@login_required
def set_temp_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = RoleExpiryForm(prefix="role")
    if form.validate_on_submit():
        user.role = UserRole.ADMIN
        user.role_expires_at = form.role_expires_at.data
        db.session.commit()
        flash("Temporary admin role set.", "success")
    else:
        flash("Invalid datetime for temporary admin role.", "danger")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/<int:user_id>/clear-admin", methods=["POST"])
@login_required
def clear_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.role = UserRole.USER
    user.role_expires_at = None
    db.session.commit()
    flash("Admin role removed.", "info")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/windows", methods=["GET", "POST"])
@login_required
def windows():
    form = AccessWindowForm()
    form.user_id.choices = [(u.user_id, u.email) for u in User.query.order_by(User.email.asc()).all()]

    if form.validate_on_submit():
        start = form.start_time.data
        end = form.end_time.data
        if end <= start:
            flash("End time must be after start time.", "danger")
            return redirect(url_for("admin.windows"))
        window = AccessWindow(user_id=form.user_id.data, start_time=start, end_time=end)
        db.session.add(window)
        db.session.commit()
        flash("Access window created.", "success")
        return redirect(url_for("admin.windows"))

    windows_list = AccessWindow.query.order_by(AccessWindow.start_time.desc()).limit(200).all()
    return render_template("set_windows.html", form=form, windows=windows_list)


@admin_bp.route("/logs")
@login_required
def logs():
    query = AccessLog.query
    user_id = request.args.get("user_id", type=int)
    result = request.args.get("result", type=str)
    from_date = request.args.get("from")

    if user_id:
        query = query.filter(AccessLog.user_id == user_id)
    if result in {AccessResult.GRANT.value, AccessResult.DENY.value}:
        query = query.filter(AccessLog.result == AccessResult(result))
    if from_date:
        try:
            dt = datetime.fromisoformat(from_date)
            query = query.filter(AccessLog.timestamp >= dt)
        except ValueError:
            flash("Invalid date filter format. Use ISO format.", "warning")

    logs_list = query.order_by(AccessLog.timestamp.desc()).limit(500).all()
    users = User.query.order_by(User.email.asc()).all()
    return render_template("view_logs.html", logs=logs_list, users=users)
