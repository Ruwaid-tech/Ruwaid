from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .forms import AccessAttemptForm
from .models import AccessLog, AccessWindow, UserStatus
from .security import process_access_attempt


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = AccessAttemptForm()
    latest_window = (
        AccessWindow.query.filter_by(user_id=current_user.user_id).order_by(AccessWindow.end_time.desc()).first()
    )

    result_message = None
    if form.validate_on_submit():
        ok, message = process_access_attempt(
            current_user.user_id,
            form.pin.data,
            datetime.utcnow(),
            request.remote_addr,
        )
        category = "success" if ok else "danger"
        flash(message, category)
        result_message = message

    return render_template(
        "dashboard.html",
        form=form,
        latest_window=latest_window,
        result_message=result_message,
        can_attempt=current_user.status == UserStatus.ACTIVE and current_user.email_confirmed,
    )


@main_bp.route("/my-history")
@login_required
def my_history():
    logs = (
        AccessLog.query.filter_by(user_id=current_user.user_id).order_by(AccessLog.timestamp.desc()).limit(200).all()
    )
    return render_template("my_history.html", logs=logs)


@main_bp.route("/user/<int:user_id>/history")
@login_required
def forbidden_user_history(user_id):
    if user_id != current_user.user_id:
        abort(403)
    return redirect(url_for("main.my_history"))
