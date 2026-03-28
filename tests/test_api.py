import pytest
import json
from api import create_token


class TestAPIAuth:
    """Test API authentication."""

    def test_login_no_data(self, client):
        """Test API login with no data."""
        response = client.post("/api/v1/auth/login", content_type="application/json")
        assert response.status_code == 400

    def test_login_invalid_credentials(self, client):
        """Test API login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "nonexistent", "password": "wrong"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_login_success(self, client, test_user):
        """Test successful API login."""
        response = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "testuser", "password": "TestPass123!"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "token" in data["data"]

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["data"]["status"] == "healthy"


class TestAPIProducts:
    """Test API products endpoints."""

    def test_products_unauthorized(self, client):
        """Test products without auth."""
        response = client.get("/api/v1/products")
        assert response.status_code == 401

    def test_products_with_auth(self, client, test_user, test_product):
        """Test products with auth."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            "/api/v1/products", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data

    def test_products_pagination(self, client, test_user, test_product):
        """Test products pagination."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            "/api/v1/products?page=1&per_page=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "pagination" in data["data"] or data.get("pagination") is not None

    def test_product_detail(self, client, test_user, test_product):
        """Test product detail."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            f"/api/v1/products/{test_product.product_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["data"]["name"] == test_product.product_name


class TestAPICustomers:
    """Test API customer endpoints."""

    def test_customers_with_auth(self, client, test_user, test_customer):
        """Test customers with auth."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            "/api/v1/customers", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_customer_detail(self, client, test_user, test_customer):
        """Test customer detail."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            f"/api/v1/customers/{test_customer.customer_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["data"]["name"] == test_customer.full_name


class TestAPIInvoices:
    """Test API invoice endpoints."""

    def test_invoices_with_auth(self, client, test_user, test_customer):
        """Test invoices with auth."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            "/api/v1/invoices", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_invoices_pagination(self, client, test_user):
        """Test invoices pagination."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            "/api/v1/invoices?page=1&per_page=20",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get("pagination") is not None


class TestAPIStock:
    """Test API stock endpoints."""

    def test_stock_with_auth(self, client, test_user, test_product):
        """Test stock with auth."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            "/api/v1/stock", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_stock_movements(self, client, test_user):
        """Test stock movements."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            "/api/v1/stock/movements", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


class TestAPIDashboard:
    """Test API dashboard endpoint."""

    def test_dashboard_with_auth(self, client, test_user):
        """Test dashboard with auth."""
        token = create_token(test_user.user_id, test_user.username, test_user.role)
        response = client.get(
            "/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "stats" in data["data"]


class TestAPIErrorHandling:
    """Test API error handling."""

    def test_invalid_token(self, client):
        """Test invalid token."""
        response = client.get(
            "/api/v1/products", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_missing_token(self, client):
        """Test missing token."""
        response = client.get("/api/v1/products")
        assert response.status_code == 401

    def test_api_docs(self, client):
        """Test API docs endpoint."""
        response = client.get("/api/v1/docs")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "endpoints" in data["data"]
