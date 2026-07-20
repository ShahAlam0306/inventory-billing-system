from datetime import datetime, timedelta
from io import BytesIO
import click
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, send_file
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)

from config import Config
from models import db, User, Product, Bill, BillItem, Category

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------- Auth ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------- Dashboard ----------

@app.route("/")
@login_required
def dashboard():
    low_stock = Product.query.filter(Product.stock_qty <= Product.reorder_level).all()
    today = datetime.utcnow().date()
    today_bills = Bill.query.filter(db.func.date(Bill.date) == today).all()
    today_total = sum(b.total_amount for b in today_bills)

    total_products = Product.query.count()

    total_revenue = db.session.query(db.func.sum(Bill.total_amount)).scalar() or 0
    total_bills_count = Bill.query.count()
    average_bill = (total_revenue / total_bills_count) if total_bills_count else 0

    best_product_row = (
        db.session.query(Product.name, db.func.sum(BillItem.qty).label("qty_sold"))
        .join(BillItem, BillItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(db.desc("qty_sold"))
        .first()
    )
    best_product = {"name": best_product_row.name, "qty": best_product_row.qty_sold} if best_product_row else None

    recent_bills = Bill.query.order_by(Bill.date.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        low_stock=low_stock,
        today_total=today_total,
        today_count=len(today_bills),
        total_products=total_products,
        total_revenue=total_revenue,
        average_bill=average_bill,
        best_product=best_product,
        recent_bills=recent_bills,
    )


@app.route("/api/sales-last-7-days")
@login_required
def sales_last_7_days():
    """JSON feed for the Chart.js dashboard graph — daily view."""
    data = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        total = (
            db.session.query(db.func.sum(Bill.total_amount))
            .filter(db.func.date(Bill.date) == day)
            .scalar() or 0
        )
        data.append({"day": day.strftime("%a"), "total": round(total, 2)})
    return jsonify(data)


@app.route("/api/sales-weekly")
@login_required
def sales_weekly():
    """JSON feed for the dashboard graph — last 8 weeks, Monday-to-Sunday."""
    data = []
    today = datetime.utcnow().date()
    start_of_this_week = today - timedelta(days=today.weekday())
    for i in range(7, -1, -1):
        week_start = start_of_this_week - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        total = (
            db.session.query(db.func.sum(Bill.total_amount))
            .filter(db.func.date(Bill.date) >= week_start, db.func.date(Bill.date) <= week_end)
            .scalar() or 0
        )
        data.append({"day": week_start.strftime("%d %b"), "total": round(total, 2)})
    return jsonify(data)


@app.route("/api/sales-monthly")
@login_required
def sales_monthly():
    """JSON feed for the dashboard graph — last 6 calendar months."""
    data = []
    today = datetime.utcnow().date()
    year, month = today.year, today.month

    months = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    for (y, m) in months:
        start = datetime(y, m, 1).date()
        end = (datetime(y + 1, 1, 1).date() - timedelta(days=1)) if m == 12 \
            else (datetime(y, m + 1, 1).date() - timedelta(days=1))
        total = (
            db.session.query(db.func.sum(Bill.total_amount))
            .filter(db.func.date(Bill.date) >= start, db.func.date(Bill.date) <= end)
            .scalar() or 0
        )
        data.append({"day": start.strftime("%b %Y"), "total": round(total, 2)})
    return jsonify(data)


# ---------- Inventory ----------

@app.route("/inventory")
@login_required
def inventory():
    products = Product.query.order_by(Product.name).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template("inventory.html", products=products, categories=categories)


def _get_or_create_category(name):
    """Case-insensitive lookup; creates the category if it doesn't exist yet."""
    name = name.strip()
    if not name:
        return None
    cat = Category.query.filter(db.func.lower(Category.name) == name.lower()).first()
    if not cat:
        cat = Category(name=name)
        db.session.add(cat)
        db.session.flush()  # assigns cat.id without committing yet
    return cat


def _validate_product_form(form):
    """Returns (is_valid, error_message, cleaned_data). Shared by add/edit."""
    name = form.get("name", "").strip()
    if not name:
        return False, "Product name cannot be empty.", None

    category = form.get("category", "").strip()
    if not category:
        return False, "Category cannot be empty.", None

    try:
        price = float(form.get("price", ""))
    except ValueError:
        return False, "Price must be a valid number.", None
    if price < 0:
        return False, "Price cannot be negative.", None

    try:
        stock_qty = int(form.get("stock_qty", ""))
    except ValueError:
        return False, "Stock quantity must be a whole number.", None
    if stock_qty < 0:
        return False, "Stock quantity cannot be negative.", None

    try:
        reorder_level = int(form.get("reorder_level") or 10)
    except ValueError:
        return False, "Reorder level must be a whole number.", None
    if reorder_level < 0:
        return False, "Reorder level cannot be negative.", None

    cleaned = {
        "name": name,
        "category": category,
        "price": price,
        "stock_qty": stock_qty,
        "reorder_level": reorder_level,
    }
    return True, None, cleaned


@app.route("/inventory/add", methods=["POST"])
@login_required
def add_product():
    is_valid, error, data = _validate_product_form(request.form)
    if not is_valid:
        flash(error)
        return redirect(url_for("inventory"))

    category = _get_or_create_category(data.pop("category"))
    p = Product(category_id=category.id, **data)
    db.session.add(p)
    db.session.commit()
    flash(f"Added {p.name}")
    return redirect(url_for("inventory"))


@app.route("/inventory/<int:product_id>/edit", methods=["POST"])
@login_required
def edit_product(product_id):
    p = Product.query.get_or_404(product_id)

    is_valid, error, data = _validate_product_form(request.form)
    if not is_valid:
        flash(error)
        return redirect(url_for("inventory"))

    category = _get_or_create_category(data["category"])
    p.name = data["name"]
    p.category_id = category.id
    p.price = data["price"]
    p.stock_qty = data["stock_qty"]
    p.reorder_level = data["reorder_level"]
    db.session.commit()
    flash(f"Updated {p.name}")
    return redirect(url_for("inventory"))


@app.route("/inventory/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    p = Product.query.get_or_404(product_id)

    # Check if this product has already been sold
    items = BillItem.query.filter_by(product_id=product_id).first()

    if items:
        flash("Cannot delete a product that has already been sold.")
        return redirect(url_for("inventory"))

    db.session.delete(p)
    db.session.commit()

    flash(f"Deleted {p.name}")
    return redirect(url_for("inventory"))


# ---------- Billing / POS ----------

@app.route("/billing")
@login_required
def billing():
    products = Product.query.order_by(Product.name).all()
    return render_template("billing.html", products=products)


@app.route("/billing/checkout", methods=["POST"])
@login_required
def checkout():
    """
    Expects JSON: {"items": [{"product_id": 1, "qty": 2}, ...]}
    Creates the bill, snapshots price, and deducts stock in one transaction.
    """
    payload = request.get_json(silent=True) or {}
    cart = payload.get("items", [])
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    bill = Bill(cashier_id=current_user.id, total_amount=0)
    db.session.add(bill)

    total = 0.0
    for entry in cart:
        product = Product.query.get(entry.get("product_id"))

        try:
            qty = int(entry.get("qty", 0))
        except (TypeError, ValueError):
            db.session.rollback()
            return jsonify({"error": "Invalid quantity in cart"}), 400

        if qty <= 0:
            db.session.rollback()
            return jsonify({"error": "Quantity must be greater than zero"}), 400

        if not product or product.stock_qty < qty:
            db.session.rollback()
            return jsonify({"error": f"Not enough stock for {product.name if product else 'item'}"}), 400

        product.stock_qty -= qty  # auto stock deduction
        item = BillItem(bill=bill, product=product, qty=qty, price_at_sale=product.price)
        db.session.add(item)
        total += qty * product.price

    bill.total_amount = round(total, 2)
    db.session.commit()
    return jsonify({"bill_id": bill.id, "total": bill.total_amount})


# ---------- Sales history ----------

@app.route("/bills")
@login_required
def bills():
    all_bills = Bill.query.order_by(Bill.date.desc()).all()
    return render_template("bills.html", bills=all_bills)


@app.route("/bills/<int:bill_id>")
@login_required
def bill_detail(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    return render_template("bill_detail.html", bill=bill)


# ---------- Branded PDF invoice ----------

BRAND_DARK = colors.HexColor("#7a3b2e")
BRAND_LIGHT = colors.HexColor("#f4ece3")
TEXT_GRAY = colors.HexColor("#555555")

SHOP_NAME = "S.S.A. General Store"
SHOP_TAGLINE = "Your neighbourhood shop, done digitally"


def _build_invoice_pdf(bill):
    """Builds a branded A4 invoice PDF for the given Bill and returns a BytesIO buffer."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    shop_name_style = ParagraphStyle(
        "ShopName", parent=styles["Title"], fontSize=20, textColor=BRAND_DARK,
        alignment=TA_CENTER, spaceAfter=2,
    )
    tagline_style = ParagraphStyle(
        "Tagline", parent=styles["Normal"], fontSize=9, textColor=TEXT_GRAY,
        alignment=TA_CENTER, spaceAfter=14,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"], fontSize=10, textColor=TEXT_GRAY,
        alignment=TA_RIGHT,
    )
    invoice_title_style = ParagraphStyle(
        "InvoiceTitle", parent=styles["Heading2"], fontSize=14, textColor=BRAND_DARK,
        alignment=TA_RIGHT, spaceAfter=4,
    )
    thanks_style = ParagraphStyle(
        "Thanks", parent=styles["Normal"], fontSize=10, textColor=TEXT_GRAY,
        alignment=TA_CENTER,
    )

    elements = []
    elements.append(Paragraph(SHOP_NAME, shop_name_style))
    elements.append(Paragraph(SHOP_TAGLINE, tagline_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=BRAND_DARK, spaceAfter=14))

    elements.append(Paragraph("INVOICE", invoice_title_style))
    elements.append(Paragraph(f"Bill #{bill.id}", meta_style))
    elements.append(Paragraph(bill.date.strftime("%d %b %Y, %I:%M %p"), meta_style))
    elements.append(Paragraph(f"Cashier: {bill.cashier.name if bill.cashier else '-'}", meta_style))
    elements.append(Spacer(1, 16))

    data = [["Product", "Qty", "Price", "Subtotal"]]
    for item in bill.items:
        data.append([
            item.product.name,
            str(item.qty),
            f"Rs. {item.price_at_sale:.2f}",
            f"Rs. {item.subtotal:.2f}",
        ])
    data.append(["", "", "Total", f"Rs. {bill.total_amount:.2f}"])

    table = Table(data, colWidths=[70 * mm, 25 * mm, 35 * mm, 35 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_LIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_DARK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),

        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -2), 10),
        ("TOPPADDING", (0, 1), (-1, -2), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 8),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, colors.HexColor("#eeeeee")),

        ("LINEABOVE", (0, -1), (-1, -1), 1.5, BRAND_DARK),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (2, -1), (-1, -1), 12),
        ("TOPPADDING", (0, -1), (-1, -1), 12),
        ("SPAN", (0, -1), (1, -1)),

        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Thank you for shopping with us!", thanks_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


@app.route("/bills/<int:bill_id>/pdf")
@login_required
def bill_pdf(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    buffer = _build_invoice_pdf(bill)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Invoice_{bill.id}.pdf",
        mimetype="application/pdf",
    )


# ---------- One-time setup helper ----------

@app.cli.command("seed")
def seed():
    """Run with: flask --app app seed  -- creates tables + a default admin user."""
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(
            name="Admin",
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        print("Created admin user -> username: admin | password: admin123")
    else:
        print("Admin user already exists")


@app.cli.command("create-user")
@click.argument("username")
@click.argument("password")
@click.argument("name")
@click.option("--role", default="cashier", help="admin or cashier")
def create_user(username, password, name, role):
    """
    Run with: flask --app app create-user <username> <password> <name> --role admin|cashier
    Example:  flask --app app create-user sohail sohail123 "Sohail" --role cashier
    """
    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists — pick a different username.")
        return

    u = User(
        name=name,
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(u)
    db.session.commit()
    print(f"Created user '{username}' ({name}), role={role}")


if __name__ == "__main__":
    app.run(debug=True)