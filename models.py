from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    force_password_change = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.Index('idx_user_username', 'username'),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'


class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.Index('idx_customer_name', 'first_name', 'last_name'),
        db.Index('idx_customer_phone', 'phone_number'),
    )

    invoices = db.relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, primary_key=True)
    product_type = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_model = db.Column(db.String(255), nullable=False)
    product_color = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    __table_args__ = (
        db.Index('idx_product_name', 'product_name'),
        db.Index('idx_product_type', 'product_type'),
    )

    invoice_items = db.relationship("InvoiceItem", back_populates="product")
    stock_movements = db.relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")

    @property
    def is_low_stock(self):
        return self.product_quantity <= self.low_stock_threshold


class StockMovement(db.Model):
    __tablename__ = 'stock_movement'
    movement_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.product_id"), nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(50), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    created_by = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.Index('idx_stock_movement_product', 'product_id'),
        db.Index('idx_stock_movement_type', 'movement_type'),
    )

    product = db.relationship("Product", back_populates="stock_movements")


class Invoice(db.Model):
    __tablename__ = 'invoice'
    invoice_id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_details = db.Column(db.Integer, db.ForeignKey("customer.customer_id"), nullable=False)
    status = db.Column(db.String(50), default='draft')
    subtotal = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_reference = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    __table_args__ = (
        db.Index('idx_invoice_customer', 'customer_details'),
        db.Index('idx_invoice_number', 'invoice_number'),
        db.Index('idx_invoice_status', 'status'),
    )

    customer = db.relationship("Customer", back_populates="invoices")
    items = db.relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    @property
    def is_paid(self):
        return self.status == 'paid'

    @property
    def is_pending(self):
        return self.status in ['pending', 'draft']

    @property
    def can_edit(self):
        return self.status in ['draft', 'pending']

    @property
    def can_cancel(self):
        return self.status in ['draft', 'pending']

    @staticmethod
    def generate_invoice_number():
        today = datetime.now()
        count = Invoice.query.filter(
            Invoice.invoice_number.like(f"INV-{today.strftime('%Y%m%d')}-%")
        ).count() + 1
        return f"INV-{today.strftime('%Y%m%d')}-{count:04d}"

    def calculate_totals(self):
        self.subtotal = sum(item.total for item in self.items)
        tax_rate = self.tax_rate or 0
        self.tax_amount = self.subtotal * (tax_rate / 100)
        discount = self.discount_amount or 0
        self.total = self.subtotal + self.tax_amount - discount


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_item'
    item_id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.invoice_id"), nullable=False)
    product_details = db.Column(db.Integer, db.ForeignKey("product.product_id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.Index('idx_invoice_item_invoice', 'invoice_id'),
        db.Index('idx_invoice_item_product', 'product_details'),
    )

    invoice = db.relationship("Invoice", back_populates="items")
    product = db.relationship("Product", back_populates="invoice_items")

    def calculate_total(self):
        discount_pct = self.discount_percent or 0
        line_total = self.unit_price * self.quantity
        self.discount_amount = line_total * (discount_pct / 100)
        self.total = line_total - self.discount_amount
