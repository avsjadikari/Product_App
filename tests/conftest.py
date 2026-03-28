import os
import pytest
from datetime import datetime

os.environ.setdefault("FLASK_ENV", "testing")

from app import app, db
from models import User, Customer, Product, Invoice, InvoiceItem


@pytest.fixture(scope="session")
def test_app():
    """Create application for testing."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["JWT_SECRET_KEY"] = "test-jwt-secret"

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="function")
def client(test_app):
    """Create test client."""
    return test_app.test_client()


@pytest.fixture(scope="function")
def db_session(test_app):
    """Create database session for testing."""
    with test_app.app_context():
        db.session.begin_nested()
        yield db.session
        db.session.rollback()


@pytest.fixture
def test_user(test_app):
    """Create test user."""
    with test_app.app_context():
        user = User(username="testuser", role="user")
        user.set_password("TestPass123!")
        db.session.add(user)
        db.session.commit()

        yield user

        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def admin_user(test_app):
    """Create admin user."""
    with test_app.app_context():
        user = User(username="admin", role="admin")
        user.set_password("AdminPass123!")
        db.session.add(user)
        db.session.commit()

        yield user

        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def test_customer(test_app):
    """Create test customer."""
    with test_app.app_context():
        customer = Customer(
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            customer_address="123 Test St",
            email="john@test.com",
        )
        db.session.add(customer)
        db.session.commit()

        yield customer

        db.session.delete(customer)
        db.session.commit()


@pytest.fixture
def test_product(test_app):
    """Create test product."""
    with test_app.app_context():
        product = Product(
            product_type="Laptop",
            product_name="Test Laptop",
            product_model="X1",
            product_color="Black",
            product_price=999.99,
            product_quantity=10,
            low_stock_threshold=5,
        )
        db.session.add(product)
        db.session.commit()

        yield product

        db.session.delete(product)
        db.session.commit()


@pytest.fixture
def authenticated_client(client, test_user):
    """Create authenticated test client."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user.user_id
        sess["username"] = test_user.username
        sess["role"] = test_user.role
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Create admin authenticated test client."""
    with client.session_transaction() as sess:
        sess["user_id"] = admin_user.user_id
        sess["username"] = admin_user.username
        sess["role"] = admin_user.role
    return client
