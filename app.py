from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import Config
from models import db, User, MenuItem, Order, OrderItem
from services.order_service import create_order_from_cart

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None

@app.context_processor
def inject_user():
    return {"current_user": current_user()}

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        if user.role != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("menu"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    return redirect(url_for("menu"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("menu"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or len(name) < 2:
            flash("Enter a valid name.", "danger")
        elif "@" not in email or len(email) < 5:
            flash("Enter a valid email.", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password), role="student")
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("admin_dashboard" if current_user().role == "admin" else "menu"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
        else:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("admin_dashboard" if user.role == "admin" else "menu"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/menu")
def menu():
    query = request.args.get("q", "").strip()
    items_query = MenuItem.query.filter_by(is_available=True)
    if query:
        items_query = items_query.filter(MenuItem.name.ilike(f"%{query}%"))
    items = items_query.order_by(MenuItem.name).all()
    return render_template("menu.html", items=items, query=query)

@app.route("/cart")
@login_required
def cart():
    cart_data = session.get("cart", {})
    ids = [int(k) for k in cart_data.keys()]
    items = MenuItem.query.filter(MenuItem.id.in_(ids), MenuItem.is_available.is_(True)).all() if ids else []
    lines, total = [], 0.0
    for item in items:
        qty = max(1, int(cart_data.get(str(item.id), 1)))
        qty = min(qty, item.stock)
        if qty > 0:
            subtotal = item.price * qty
            total += subtotal
            lines.append({"item": item, "quantity": qty, "subtotal": subtotal})
    return render_template("cart.html", lines=lines, total=total)

@app.route("/cart/add/<int:item_id>", methods=["POST"])
@login_required
def add_to_cart(item_id):
    item = db.session.get(MenuItem, item_id)
    if not item or not item.is_available:
        flash("Menu item is unavailable.", "danger")
        return redirect(url_for("menu"))
    if item.stock < 1:
        flash("This item is out of stock.", "danger")
        return redirect(url_for("menu"))
    cart_data = session.get("cart", {})
    key = str(item_id)
    new_qty = int(cart_data.get(key, 0)) + 1
    if new_qty > item.stock:
        flash(f"Only {item.stock} unit(s) available.", "warning")
        new_qty = item.stock
    cart_data[key] = new_qty
    session["cart"] = cart_data
    flash(f"{item.name} added to cart.", "success")
    return redirect(request.referrer or url_for("menu"))

@app.route("/cart/update", methods=["POST"])
@login_required
def update_cart():
    cart_data = session.get("cart", {})
    for key in list(cart_data.keys()):
        raw = request.form.get(f"qty_{key}")
        try:
            qty = int(raw)
        except (TypeError, ValueError):
            qty = 1
        item = db.session.get(MenuItem, int(key))
        if not item or not item.is_available or item.stock < 1 or qty <= 0:
            cart_data.pop(key, None)
        else:
            cart_data[key] = min(qty, item.stock)
    session["cart"] = cart_data
    flash("Cart updated.", "success")
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    cart_data = session.get("cart", {})
    cart_data.pop(str(item_id), None)
    session["cart"] = cart_data
    return redirect(url_for("cart"))

@app.route("/orders/place", methods=["POST"])
@login_required
def place_order():
    cart_data = session.get("cart", {})
    try:
        order = create_order_from_cart(current_user().id, cart_data)
        db.session.commit()
        session["cart"] = {}
        flash(f"Order #{order.id} placed successfully.", "success")
        return redirect(url_for("order_history"))
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
        return redirect(url_for("cart"))

@app.route("/orders")
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user().id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)

@app.route("/admin")
@admin_required
def admin_dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    items = MenuItem.query.order_by(MenuItem.name).all()
    return render_template("admin/dashboard.html", orders=orders, items=items)

@app.route("/admin/items/add", methods=["POST"])
@admin_required
def admin_add_item():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    try:
        price = float(request.form.get("price", ""))
        stock = int(request.form.get("stock", ""))
    except ValueError:
        flash("Price and stock must be valid numbers.", "danger")
        return redirect(url_for("admin_dashboard"))
    if not name or price <= 0 or stock < 0:
        flash("Enter valid item details.", "danger")
        return redirect(url_for("admin_dashboard"))
    db.session.add(MenuItem(name=name, description=description, category=category or "General",
                            price=round(price, 2), stock=stock, is_available=True))
    db.session.commit()
    flash("Menu item added.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/items/<int:item_id>/edit", methods=["POST"])
@admin_required
def admin_edit_item(item_id):
    item = db.session.get(MenuItem, item_id)
    if not item:
        flash("Menu item not found.", "danger")
        return redirect(url_for("admin_dashboard"))
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    try:
        price = float(request.form.get("price", ""))
        stock = int(request.form.get("stock", ""))
    except ValueError:
        flash("Price and stock must be valid numbers.", "danger")
        return redirect(url_for("admin_dashboard"))
    if not name or price <= 0 or stock < 0:
        flash("Enter valid item details.", "danger")
        return redirect(url_for("admin_dashboard"))
    item.name, item.description, item.category = name, description, category or "General"
    item.price, item.stock = round(price, 2), stock
    item.is_available = stock > 0
    db.session.commit()
    flash("Menu item updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/items/<int:item_id>/delete", methods=["POST"])
@admin_required
def admin_delete_item(item_id):
    item = db.session.get(MenuItem, item_id)
    if item:
        item.is_available = False
        item.stock = 0
        db.session.commit()
        flash("Menu item removed from the active menu.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_order_status(order_id):
    order = db.session.get(Order, order_id)
    status = request.form.get("status", "")
    allowed = {"Pending", "Preparing", "Ready", "Completed", "Cancelled"}
    if not order or status not in allowed:
        flash("Invalid order status.", "danger")
        return redirect(url_for("admin_dashboard"))
    order.status = status
    db.session.commit()
    flash(f"Order #{order.id} status updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="Page not found."), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(app.config.get("PORT", 5000)), debug=True)
