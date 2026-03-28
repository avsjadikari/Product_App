import pytest
import json


class TestAuthRoutes:
    """Test authentication routes."""

    def test_login_page_loads(self, client):
        """Test login page loads."""
        response = client.get("/login")
        assert response.status_code == 200

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "TestPass123!"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_login_invalid_credentials(self, client, test_user):
        """Test invalid login."""
        response = client.post(
            "/login", data={"username": "testuser", "password": "WrongPass"}
        )
        assert b"Invalid username or password" in response.data

    def test_logout(self, authenticated_client):
        """Test logout."""
        response = authenticated_client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"logged out" in response.data.lower()


class TestDashboardRoutes:
    """Test dashboard routes."""

    def test_home_requires_login(self, client):
        """Test home requires login."""
        response = client.get("/")
        assert response.status_code == 302

    def test_home_authenticated(self, authenticated_client):
        """Test home page for authenticated user."""
        response = authenticated_client.get("/")
        assert response.status_code == 200


class TestProductRoutes:
    """Test product routes."""

    def test_products_list(self, authenticated_client):
        """Test products list page."""
        response = authenticated_client.get("/products")
        assert response.status_code == 200

    def test_add_product(self, authenticated_client):
        """Test adding a product."""
        response = authenticated_client.post(
            "/products/add",
            data={
                "product_type": "Test",
                "product_name": "Test Product",
                "product_model": "T1",
                "product_color": "Black",
                "product_price": 100.0,
                "product_quantity": 10,
                "low_stock_threshold": 5,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200


class TestCustomerRoutes:
    """Test customer routes."""

    def test_customers_list(self, authenticated_client):
        """Test customers list page."""
        response = authenticated_client.get("/customers")
        assert response.status_code == 200

    def test_add_customer(self, authenticated_client):
        """Test adding a customer."""
        response = authenticated_client.post(
            "/customers/add",
            data={
                "first_name": "Test",
                "last_name": "Customer",
                "phone_number": "1234567890",
                "customer_address": "123 Test St",
                "email": "test@test.com",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200


class TestCartRoutes:
    """Test cart routes."""

    def test_cart_empty(self, authenticated_client):
        """Test empty cart."""
        response = authenticated_client.get("/cart")
        assert response.status_code == 200

    def test_add_to_cart(self, authenticated_client, test_product):
        """Test adding product to cart."""
        response = authenticated_client.post(
            f"/cart/add/{test_product.product_id}",
            data={"quantity": 1},
            follow_redirects=True,
        )
        assert response.status_code == 200


class TestInvoiceRoutes:
    """Test invoice routes."""

    def test_invoices_list(self, authenticated_client):
        """Test invoices list page."""
        response = authenticated_client.get("/invoices")
        assert response.status_code == 200


class TestReportRoutes:
    """Test report routes."""

    def test_sales_report(self, authenticated_client):
        """Test sales report page."""
        response = authenticated_client.get("/reports/sales")
        assert response.status_code == 200

    def test_stock_report(self, authenticated_client):
        """Test stock report page."""
        response = authenticated_client.get("/reports/stock")
        assert response.status_code == 200


class TestExportRoutes:
    """Test export routes."""

    def test_export_products(self, authenticated_client):
        """Test exporting products."""
        response = authenticated_client.get("/export/products")
        assert response.status_code == 200
        assert "text/csv" in response.content_type

    def test_export_customers(self, authenticated_client):
        """Test exporting customers."""
        response = authenticated_client.get("/export/customers")
        assert response.status_code == 200
        assert "text/csv" in response.content_type


class TestSearchRoutes:
    """Test search routes."""

    def test_search_products_ajax(self, authenticated_client, test_product):
        """Test AJAX product search."""
        response = authenticated_client.get(
            f"/search/products?q={test_product.product_name}"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_search_customers_ajax(self, authenticated_client, test_customer):
        """Test AJAX customer search."""
        response = authenticated_client.get(
            f"/search/customers?q={test_customer.first_name}"
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
