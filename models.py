from datetime import datetime
import threading

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"
    __allow_unmapped__ = True

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")
    is_active = db.Column(db.Boolean, default=True)
    force_password_change = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (Index("idx_user_username", "username"),)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Customer(db.Model):
    __tablename__ = "customer"
    __allow_unmapped__ = True

    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_active = db.Column(db.Boolean, default=True)

    __table_args__ = (
        Index("idx_customer_name", "first_name", "last_name"),
        Index("idx_customer_phone", "phone_number"),
    )

    invoices = db.relationship(
        "Invoice", back_populates="customer", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Product(db.Model):
    __tablename__ = "product"
    __allow_unmapped__ = True

    product_id = db.Column(db.Integer, primary_key=True)
    product_type = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_model = db.Column(db.String(255), nullable=False)
    product_color = db.Column(db.String(255), nullable=False)
    product_price = db.Column(db.Numeric(10, 2), nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    __table_args__ = (
        Index("idx_product_name", "product_name"),
        Index("idx_product_type", "product_type"),
    )

    invoice_items = db.relationship("InvoiceItem", back_populates="product")
    stock_movements = db.relationship(
        "StockMovement", back_populates="product", cascade="all, delete-orphan"
    )

    @property
    def is_low_stock(self) -> bool:
        return self.product_quantity <= self.low_stock_threshold


class StockMovement(db.Model):
    __tablename__ = "stock_movement"
    __allow_unmapped__ = True

    movement_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.product_id"), nullable=False
    )
    movement_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(50), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    created_by = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        Index("idx_stock_movement_product", "product_id"),
        Index("idx_stock_movement_type", "movement_type"),
    )

    product = db.relationship("Product", back_populates="stock_movements")


class Invoice(db.Model):
    __tablename__ = "invoice"
    __allow_unmapped__ = True

    invoice_id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_details = db.Column(
        db.Integer, db.ForeignKey("customer.customer_id"), nullable=False
    )
    status = db.Column(db.String(50), default="draft")
    subtotal = db.Column(db.Numeric(10, 2), default=0)
    tax_rate = db.Column(db.Numeric(5, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_reference = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    __table_args__ = (
        Index("idx_invoice_customer", "customer_details"),
        Index("idx_invoice_number", "invoice_number"),
        Index("idx_invoice_status", "status"),
    )

    customer = db.relationship("Customer", back_populates="invoices")
    items = db.relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    _invoice_lock = threading.Lock()

    @property
    def is_paid(self) -> bool:
        return self.status == "paid"

    @property
    def is_pending(self) -> bool:
        return self.status in ["pending", "draft"]

    @property
    def can_edit(self) -> bool:
        return self.status in ["draft", "pending"]

    @property
    def can_cancel(self) -> bool:
        return self.status in ["draft", "pending"]

    @staticmethod
    def generate_invoice_number() -> str:
        with Invoice._invoice_lock:
            today = datetime.now()
            prefix = f"INV-{today.strftime('%Y%m%d')}-"

            last_invoice = (
                Invoice.query.filter(Invoice.invoice_number.like(f"{prefix}%"))
                .order_by(Invoice.invoice_number.desc())
                .first()
            )

            if last_invoice:
                try:
                    last_count = int(last_invoice.invoice_number.split("-")[-1])
                    count = last_count + 1
                except (ValueError, IndexError):
                    count = 1
            else:
                count = 1

            return f"{prefix}{count:04d}"

    def calculate_totals(self) -> None:
        from decimal import Decimal

        self.subtotal = sum(item.total for item in self.items)
        tax_rate = Decimal(str(self.tax_rate)) if self.tax_rate else Decimal("0")
        self.tax_amount = self.subtotal * (tax_rate / Decimal("100"))
        discount = (
            Decimal(str(self.discount_amount)) if self.discount_amount else Decimal("0")
        )
        self.total = self.subtotal + self.tax_amount - discount


class InvoiceItem(db.Model):
    __tablename__ = "invoice_item"
    __allow_unmapped__ = True

    item_id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer, db.ForeignKey("invoice.invoice_id"), nullable=False
    )
    product_details = db.Column(
        db.Integer, db.ForeignKey("product.product_id"), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percent = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        Index("idx_invoice_item_invoice", "invoice_id"),
        Index("idx_invoice_item_product", "product_details"),
    )

    invoice = db.relationship("Invoice", back_populates="items")
    product = db.relationship("Product", back_populates="invoice_items")

    def calculate_total(self) -> None:
        from decimal import Decimal

        discount_pct = (
            Decimal(str(self.discount_percent))
            if self.discount_percent
            else Decimal("0")
        )
        line_total = Decimal(str(self.unit_price)) * Decimal(str(self.quantity))
        self.discount_amount = line_total * (discount_pct / Decimal("100"))
        self.total = line_total - self.discount_amount
