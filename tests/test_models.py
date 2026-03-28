import pytest
from models import User, Customer, Product, Invoice, InvoiceItem


class TestUserModel:
    """Test User model."""

    def test_password_hashing(self, test_app, db_session):
        """Test password hashing."""
        user = User(username="hashtest", role="user")
        user.set_password("MyPass123!")

        assert user.password_hash != "MyPass123!"
        assert user.check_password("MyPass123!")
        assert not user.check_password("WrongPass")

    def test_is_admin(self, test_app, db_session):
        """Test admin property."""
        admin = User(username="admin", role="admin")
        user = User(username="user", role="user")

        assert admin.is_admin is True
        assert user.is_admin is False


class TestCustomerModel:
    """Test Customer model."""

    def test_full_name(self, test_app, test_customer):
        """Test full name property."""
        assert test_customer.full_name == "John Doe"


class TestProductModel:
    """Test Product model."""

    def test_is_low_stock(self, test_app, test_product):
        """Test low stock property."""
        assert test_product.is_low_stock is False

        test_product.product_quantity = 3
        assert test_product.is_low_stock is True


class TestInvoiceModel:
    """Test Invoice model."""

    def test_generate_invoice_number(self, test_app):
        """Test invoice number generation."""
        invoice_num = Invoice.generate_invoice_number()
        assert invoice_num.startswith("INV-")
        assert len(invoice_num) == 17

    def test_calculate_totals(self, test_app, test_customer, test_product):
        """Test invoice totals calculation."""
        invoice = Invoice(
            invoice_number="INV-TEST-001",
            customer_details=test_customer.customer_id,
            status="pending",
            tax_rate=10,
            discount_amount=50,
        )

        item1 = InvoiceItem(
            invoice_id=0,
            product_details=test_product.product_id,
            quantity=2,
            unit_price=100,
        )
        item1.calculate_total()

        item2 = InvoiceItem(
            invoice_id=0,
            product_details=test_product.product_id,
            quantity=1,
            unit_price=50,
            discount_percent=20,
        )
        item2.calculate_total()

        invoice.items = [item1, item2]
        invoice.calculate_totals()

        assert invoice.subtotal == 250
        assert invoice.tax_amount == 25
        assert invoice.total == 225

    def test_can_edit(self, test_app, test_customer):
        """Test can_edit property."""
        invoice_draft = Invoice(
            invoice_number="INV-TEST-001",
            customer_details=test_customer.customer_id,
            status="draft",
        )
        invoice_pending = Invoice(
            invoice_number="INV-TEST-002",
            customer_details=test_customer.customer_id,
            status="pending",
        )
        invoice_paid = Invoice(
            invoice_number="INV-TEST-003",
            customer_details=test_customer.customer_id,
            status="paid",
        )

        assert invoice_draft.can_edit is True
        assert invoice_pending.can_edit is True
        assert invoice_paid.can_edit is False

    def test_can_cancel(self, test_app, test_customer):
        """Test can_cancel property."""
        invoice_draft = Invoice(
            invoice_number="INV-TEST-001",
            customer_details=test_customer.customer_id,
            status="draft",
        )
        invoice_paid = Invoice(
            invoice_number="INV-TEST-002",
            customer_details=test_customer.customer_id,
            status="paid",
        )

        assert invoice_draft.can_cancel is True
        assert invoice_paid.can_cancel is False
