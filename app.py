import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

DATABASE = os.path.join(os.path.dirname(__file__), "arthub.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.secret_key = "super-secret-art-hub-key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------- Database helpers ----------
def get_db():
    if "db" not in g:
        if not os.path.exists(DATABASE):
            from db_init import init_db

            init_db()
        ensure_upload_folder()
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_upload_folder():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ---------- Utilities ----------
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None or session.get("role") != "ADMIN":
            flash("Admin access required.")
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def user_login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            flash("Please login to continue.")
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def get_cart():
    return session.setdefault("cart", {})


def cart_count():
    return sum(get_cart().values())


def format_currency(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0
    return f"€ {amount:,.2f}"


@app.context_processor
def inject_globals():
    return {
        "cart_count": cart_count(),
        "format_currency": format_currency,
        "current_role": session.get("role"),
    }


# ---------- Public routes ----------
@app.route("/")
def home():
    db = get_db()
    featured = db.execute(
        "SELECT * FROM artworks ORDER BY created_at DESC LIMIT 3"
    ).fetchall()
    settings = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
    return render_template("home.html", featured=featured, settings=settings)


@app.route("/about")
def about():
    db = get_db()
    settings = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
    return render_template("about.html", settings=settings)


@app.route("/gallery")
@user_login_required
def gallery():
    db = get_db()
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "All")
    sort = request.args.get("sort", "")

    query = "SELECT * FROM artworks WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if sort == "asc":
        query += " ORDER BY price ASC"
    elif sort == "desc":
        query += " ORDER BY price DESC"
    else:
        query += " ORDER BY created_at DESC"

    artworks = db.execute(query, params).fetchall()
    categories = [row[0] for row in db.execute("SELECT DISTINCT category FROM artworks").fetchall()]
    return render_template(
        "gallery.html",
        artworks=artworks,
        categories=categories,
        search=search,
        category=category,
        sort=sort,
    )


@app.route("/artwork/<int:artwork_id>")
@user_login_required
def artwork_detail(artwork_id):
    db = get_db()
    artwork = db.execute("SELECT * FROM artworks WHERE id=?", (artwork_id,)).fetchone()
    if not artwork:
        flash("Artwork not found.")
        return redirect(url_for("gallery"))
    return render_template("artwork_detail.html", artwork=artwork)


@app.route("/cart")
@user_login_required
def cart_view():
    db = get_db()
    cart = get_cart()
    artwork_ids = list(map(int, cart.keys()))
    items = []
    total = 0
    if artwork_ids:
        placeholders = ",".join(["?"] * len(artwork_ids))
        rows = db.execute(
            f"SELECT * FROM artworks WHERE id IN ({placeholders})", artwork_ids
        ).fetchall()
        for row in rows:
            qty = int(cart.get(str(row["id"]), 0))
            line_total = qty * row["price"]
            total += line_total
            items.append({"artwork": row, "qty": qty, "line_total": line_total})
    errors = session.pop("form_errors", {})
    form_data = session.pop("form_data", {})
    return render_template("cart.html", items=items, total=total, errors=errors, form_data=form_data)


@app.route("/cart/add/<int:artwork_id>", methods=["POST"])
@user_login_required
def cart_add(artwork_id):
    db = get_db()
    artwork = db.execute("SELECT stock FROM artworks WHERE id=?", (artwork_id,)).fetchone()
    if not artwork or artwork["stock"] <= 0:
        flash("Item out of stock.")
        return redirect(request.referrer or url_for("gallery"))
    qty = int(request.form.get("quantity", 1))
    if qty < 1:
        qty = 1
    cart = get_cart()
    cart[str(artwork_id)] = cart.get(str(artwork_id), 0) + qty
    session.modified = True
    return redirect(request.referrer or url_for("cart_view"))


@app.route("/cart/remove/<int:artwork_id>", methods=["POST"])
@user_login_required
def cart_remove(artwork_id):
    cart = get_cart()
    cart.pop(str(artwork_id), None)
    session.modified = True
    return redirect(url_for("cart_view"))


@app.route("/checkout", methods=["POST"])
@user_login_required
def checkout():
    db = get_db()
    cart = get_cart()
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    errors = {}
    if not cart:
        errors["cart"] = "Your cart is empty."
    if not name:
        errors["name"] = "Name is required."
    if not phone:
        errors["phone"] = "Phone is required."
    if not address:
        errors["address"] = "Address is required."

    artwork_ids = list(map(int, cart.keys()))
    items = []
    if artwork_ids:
        placeholders = ",".join(["?"] * len(artwork_ids))
        rows = db.execute(
            f"SELECT * FROM artworks WHERE id IN ({placeholders})", artwork_ids
        ).fetchall()
        for row in rows:
            qty = int(cart.get(str(row["id"]), 0))
            if qty > row["stock"]:
                errors["stock"] = "Insufficient stock for some items."
                break
            items.append({"row": row, "qty": qty})

    if errors:
        session["form_errors"] = errors
        session["form_data"] = {"name": name, "phone": phone, "address": address}
        return redirect(url_for("cart_view"))

    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    temp_code = f"TEMP-{int(datetime.now().timestamp() * 1000)}"
    cur = db.cursor()
    cur.execute(
        "INSERT INTO orders (order_code, buyer_name, phone, address, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (temp_code, name, phone, address, "Pending COD", now),
    )
    order_id = cur.lastrowid
    order_code = f"ORD-{datetime.now().year}-{order_id:05d}"
    cur.execute("UPDATE orders SET order_code=? WHERE id=?", (order_code, order_id))

    for item in items:
        row = item["row"]
        qty = item["qty"]
        cur.execute(
            "INSERT INTO order_lines (order_id, artwork_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (order_id, row["id"], qty, row["price"]),
        )
        cur.execute("UPDATE artworks SET stock = stock - ? WHERE id=?", (qty, row["id"]))
    db.commit()
    session.pop("cart", None)
    return redirect(url_for("order_confirm", order_id=order_id))


@app.route("/order/confirm/<int:order_id>")
@user_login_required
def order_confirm(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    settings = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
    if not order:
        flash("Order not found.")
        return redirect(url_for("gallery"))
    return render_template("order_confirm.html", order=order, settings=settings)


# ---------- Auth routes ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    flash("Registration is disabled. Use the provided admin credentials to login.")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    db = get_db()
    error = None
    next_url = request.args.get("next") or request.form.get("next") or url_for("gallery")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            if user["role"] != "ADMIN":
                error = "Admin access only."
            else:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                return redirect(next_url)
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error, next_url=next_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------- Admin routes ----------
@app.route("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    total_artworks = db.execute("SELECT COUNT(*) FROM artworks").fetchone()[0]
    total_orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    pending_orders = db.execute("SELECT COUNT(*) FROM orders WHERE status='Pending COD'").fetchone()[0]
    return render_template(
        "admin_dashboard.html",
        total_artworks=total_artworks,
        total_orders=total_orders,
        pending_orders=pending_orders,
    )


@app.route("/admin/orders")
@login_required
def admin_orders():
    db = get_db()
    orders = db.execute(
        "SELECT id, order_code, buyer_name, phone, status, created_at FROM orders ORDER BY created_at DESC"
    ).fetchall()
    return render_template("admin_orders.html", orders=orders)


@app.route("/admin/orders/<int:order_id>", methods=["GET", "POST"])
@login_required
def admin_order_detail(order_id):
    db = get_db()
    if request.method == "POST":
        status = request.form.get("status", "Pending COD")
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        db.commit()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        flash("Order not found.")
        return redirect(url_for("admin_orders"))
    lines = db.execute(
        """
        SELECT ol.*, a.title FROM order_lines ol
        JOIN artworks a ON a.id = ol.artwork_id
        WHERE ol.order_id=?
        """,
        (order_id,),
    ).fetchall()
    total = sum(line["quantity"] * line["unit_price"] for line in lines)
    return render_template("admin_order_detail.html", order=order, lines=lines, total=total)


@app.route("/admin/artworks")
@login_required
def admin_artworks():
    db = get_db()
    artworks = db.execute("SELECT * FROM artworks ORDER BY created_at DESC").fetchall()
    return render_template("admin_artworks.html", artworks=artworks)


@app.route("/admin/artworks/new", methods=["GET", "POST"])
@login_required
def admin_artwork_new():
    db = get_db()
    errors = {}
    artwork = None
    if request.method == "POST":
        errors, data = validate_artwork_form()
        if not errors:
            db.execute(
                "INSERT INTO artworks (title, description, image_url, category, price, stock, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    data["title"],
                    data["description"],
                    data["image_url"],
                    data["category"],
                    data["price"],
                    data["stock"],
                    datetime.now().isoformat(sep=" ", timespec="seconds"),
                ),
            )
            db.commit()
            return redirect(url_for("admin_artworks"))
    return render_template("admin_artwork_form.html", errors=errors, artwork=artwork)


@app.route("/admin/artworks/<int:artwork_id>/edit", methods=["GET", "POST"])
@login_required
def admin_artwork_edit(artwork_id):
    db = get_db()
    artwork = db.execute("SELECT * FROM artworks WHERE id=?", (artwork_id,)).fetchone()
    if not artwork:
        flash("Artwork not found.")
        return redirect(url_for("admin_artworks"))
    errors = {}
    if request.method == "POST":
        errors, data = validate_artwork_form()
        if not errors:
            db.execute(
                """
                UPDATE artworks
                SET title=?, description=?, image_url=?, category=?, price=?, stock=?
                WHERE id=?
                """,
                (
                    data["title"],
                    data["description"],
                    data["image_url"],
                    data["category"],
                    data["price"],
                    data["stock"],
                    artwork_id,
                ),
            )
            db.commit()
            return redirect(url_for("admin_artworks"))
    return render_template("admin_artwork_form.html", errors=errors, artwork=artwork)


@app.route("/admin/artworks/<int:artwork_id>/delete", methods=["POST"])
@login_required
def admin_artwork_delete(artwork_id):
    db = get_db()
    db.execute("DELETE FROM artworks WHERE id=?", (artwork_id,))
    db.commit()
    return redirect(url_for("admin_artworks"))


@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    db = get_db()
    settings = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
    errors = {}
    if request.method == "POST":
        owner_name = request.form.get("owner_name", "").strip()
        phone = request.form.get("phone", "").strip()
        alt_phone = request.form.get("alt_phone", "").strip()
        about_content = request.form.get("about_content", "").strip()
        if not owner_name:
            errors["owner_name"] = "Owner name required"
        if not phone:
            errors["phone"] = "Phone required"
        if not about_content:
            errors["about_content"] = "About content required"
        if not errors:
            if settings:
                db.execute(
                    "UPDATE settings SET owner_name=?, phone=?, alt_phone=?, about_content=? WHERE id=?",
                    (owner_name, phone, alt_phone, about_content, settings["id"]),
                )
            else:
                db.execute(
                    "INSERT INTO settings (owner_name, phone, alt_phone, about_content) VALUES (?, ?, ?, ?)",
                    (owner_name, phone, alt_phone, about_content),
                )
            db.commit()
            settings = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
            flash("Settings updated.")
    return render_template("admin_settings.html", settings=settings, errors=errors)


# ---------- Helpers ----------
def validate_artwork_form():
    errors = {}
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "0").strip()
    stock = request.form.get("stock", "0").strip()
    upload = request.files.get("image_file")
    existing_image = request.form.get("existing_image")

    try:
        price_val = float(price)
    except ValueError:
        errors["price"] = "Invalid price"
        price_val = 0.0
    try:
        stock_val = int(stock)
    except ValueError:
        errors["stock"] = "Invalid stock"
        stock_val = 0
    if not title:
        errors["title"] = "Title required"
    if not description:
        errors["description"] = "Description required"
    if not category:
        errors["category"] = "Category required"

    saved_path = None
    if upload and upload.filename:
        if allowed_file(upload.filename):
            filename = secure_filename(upload.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            upload.save(filepath)
            saved_path = url_for("static", filename=f"uploads/{filename}")
        else:
            errors["image_file"] = "Unsupported file type"

    image_final = saved_path or existing_image or request.form.get("image_url", "") or "https://via.placeholder.com/600x400?text=Art+Hub"

    data = {
        "title": title,
        "description": description,
        "image_url": image_final,
        "category": category,
        "price": price_val,
        "stock": stock_val,
    }
    return errors, data


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    app.run(debug=True)
