from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="cashier")  # 'admin' or 'cashier'


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # backref lets you write product.category.name from any Product
    products = db.relationship("Product", backref="category", lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_qty = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)

    @property
    def is_low_stock(self):
        return self.stock_qty <= self.reorder_level


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    cashier_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    total_amount = db.Column(db.Float, default=0.0)

    items = db.relationship("BillItem", backref="bill", lazy=True)
    cashier = db.relationship("User")


class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bill.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    price_at_sale = db.Column(db.Float, nullable=False)  # snapshot, price may change later

    product = db.relationship("Product")

    @property
    def subtotal(self):
        return round(self.qty * self.price_at_sale, 2)