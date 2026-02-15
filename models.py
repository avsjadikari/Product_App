from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_numbet = db.Column(db.Integer, nullable=False)
    customer_address = db.Column(db.String(255), nullable=False)

    invoices = db.relationship("Invoice", back_populates="customer")


class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, primary_key=True)
    product_type = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_color = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False)   # ✅ NEW

    invoices = db.relationship("Invoice", back_populates="product")


class Invoice(db.Model):
    __tablename__ = 'invoice'
    invoice_id = db.Column(db.Integer, primary_key=True)
    Product_details = db.Column(db.Integer, db.ForeignKey("product.product_id"), nullable=False)
    customer_details = db.Column(db.Integer, db.ForeignKey("customer.customer_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)   # ✅ NEW

    customer = db.relationship("Customer", back_populates="invoices")
    product = db.relationship("Product", back_populates="invoices")