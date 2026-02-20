from flask import render_template


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(_):
        return render_template("error.html", message="Forbidden"), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template("error.html", message="Not Found"), 404

    @app.errorhandler(500)
    def internal(_):
        return render_template("error.html", message="An unexpected error occurred."), 500
