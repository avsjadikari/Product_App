import pytest
from forms import (
    LoginForm,
    CustomerForm,
    ProductForm,
    ChangePasswordForm,
    validate_password,
)


class TestLoginForm:
    """Test LoginForm."""

    def test_valid_login_form(self):
        """Test valid login form data."""
        form = LoginForm(data={"username": "testuser", "password": "password123"})
        assert form.validate()

    def test_empty_username(self):
        """Test empty username validation."""
        form = LoginForm(data={"username": "", "password": "password123"})
        assert not form.validate()
        assert "Username" in str(form.errors)


class TestCustomerForm:
    """Test CustomerForm."""

    def test_valid_customer_form(self):
        """Test valid customer form data."""
        form = CustomerForm(
            data={
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "1234567890",
                "customer_address": "123 Main St",
                "email": "john@example.com",
            }
        )
        assert form.validate()

    def test_invalid_email(self):
        """Test invalid email validation."""
        form = CustomerForm(
            data={
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "1234567890",
                "customer_address": "123 Main St",
                "email": "invalid-email",
            }
        )
        assert not form.validate()
        assert "email" in str(form.errors).lower()


class TestProductForm:
    """Test ProductForm."""

    def test_valid_product_form(self):
        """Test valid product form data."""
        form = ProductForm(
            data={
                "product_type": "Laptop",
                "product_name": "ThinkPad",
                "product_model": "T490",
                "product_color": "Black",
                "product_price": 999.99,
                "product_quantity": 10,
                "low_stock_threshold": 5,
            }
        )
        assert form.validate()

    def test_negative_price(self):
        """Test negative price validation."""
        form = ProductForm(
            data={
                "product_type": "Laptop",
                "product_name": "ThinkPad",
                "product_model": "T490",
                "product_color": "Black",
                "product_price": -100,
                "product_quantity": 10,
                "low_stock_threshold": 5,
            }
        )
        assert not form.validate()


class TestPasswordValidation:
    """Test password validation function."""

    def test_valid_password(self):
        """Test valid password."""
        is_valid, error = validate_password("TestPass123!")
        assert is_valid
        assert error == ""

    def test_password_too_short(self):
        """Test password too short."""
        is_valid, error = validate_password("Test1!")
        assert not is_valid
        assert "at least 8 characters" in error

    def test_password_missing_uppercase(self):
        """Test password missing uppercase."""
        is_valid, error = validate_password("testpass123!")
        assert not is_valid
        assert "uppercase" in error

    def test_password_missing_lowercase(self):
        """Test password missing lowercase."""
        is_valid, error = validate_password("TESTPASS123!")
        assert not is_valid
        assert "lowercase" in error

    def test_password_missing_digit(self):
        """Test password missing digit."""
        is_valid, error = validate_password("TestPass!!")
        assert not is_valid
        assert "digit" in error

    def test_password_missing_special(self):
        """Test password missing special character."""
        is_valid, error = validate_password("TestPass123")
        assert not is_valid
        assert "special" in error
