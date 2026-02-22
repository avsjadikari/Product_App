from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.String(255), nullable=False)

    # Index for faster lookups
    __table_args__ = (
        db.Index('idx_customer_name', 'first_name', 'last_name'),
    )

    invoices = db.relationship("Invoice", back_populates="customer")


class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, primary_key=True)
    product_type = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_model = db.Column(db.String(255), nullable=False)
    product_color = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False, default=0)

    # Index for faster lookups
    __table_args__ = (
        db.Index('idx_product_name', 'product_name'),
        db.Index('idx_product_type', 'product_type'),
    )

    invoices = db.relationship("Invoice", back_populates="product")


class Invoice(db.Model):
    __tablename__ = 'invoice'
    invoice_id = db.Column(db.Integer, primary_key=True)
    product_details = db.Column(db.Integer, db.ForeignKey("product.product_id"), nullable=False)
    customer_details = db.Column(db.Integer, db.ForeignKey("customer.customer_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Indexes for foreign keys (critical for JOIN performance)
    __table_args__ = (
        db.Index('idx_invoice_customer', 'customer_details'),
        db.Index('idx_invoice_product', 'product_details'),
    )

    customer = db.relationship("Customer", back_populates="invoices")
    product = db.relationship("Product", back_populates="invoices")
