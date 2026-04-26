"""
RESTful API endpoints for the POS application.
Provides JSON endpoints for mobile apps and external integrations.
"""

from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional

import jwt
from flask import Blueprint, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash

from models import db, User, Product, Customer, Invoice, InvoiceItem, StockMovement
from config import Config

api = Blueprint("api", __name__, url_prefix="/api/v1")

import logging

api_logger = logging.getLogger(__name__)

SWAGGER_UI_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Product App API Documentation</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui.css">
    <style>
        body { margin: 0; padding: 0; }
        .swagger-ui .topbar { display: none; }
        .swagger-ui .info .title { font-size: 2.5rem; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: "/api/v1/openapi.json",
                dom_id: "#swagger-ui",
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout",
                docExpansion: "list"
            });
        };
    </script>
</body>
</html>
'''

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Product App API",
        "description": "RESTful API for the POS Application. Provides endpoints for managing products, customers, invoices, and stock.",
        "version": "1.0.0"
    },
    "servers": [{"url": "/api/v1", "description": "Current API version"}],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "paths": {
        "/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Health check endpoint",
                "responses": {"200": {"description": "Service is healthy"}}
            }
        },
        "/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Authenticate and get JWT token",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["username", "password"],
                                "properties": {
                                    "username": {"type": "string"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Login successful"}}
            }
        },
        "/products": {
            "get": {
                "tags": ["Products"],
                "summary": "Get all products",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "List of products"}}
            }
        },
        "/customers": {
            "get": {
                "tags": ["Customers"],
                "summary": "Get all customers",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "List of customers"}}
            }
        },
        "/invoices": {
            "get": {
                "tags": ["Invoices"],
                "summary": "Get all invoices",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "List of invoices"}}
            }
        },
        "/stock": {
            "get": {
                "tags": ["Stock"],
                "summary": "Get stock levels",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Stock levels"}}
            }
        },
        "/dashboard": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Get dashboard statistics",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Dashboard stats"}}
            }
        }
    }
}


def create_token(user_id: int, username: str, role: str) -> str:
    """Create JWT token for authenticated user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def jwt_required(f: Callable) -> Callable:
    """Decorator to require JWT authentication for API endpoints."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify(
                {"error": "Authorization header required", "code": "NO_TOKEN"}
            ), 401

        token = auth_header[7:]
        payload = decode_token(token)

        if not payload:
            return jsonify(
                {"error": "Invalid or expired token", "code": "INVALID_TOKEN"}
            ), 401

        request.api_user = payload
        return f(*args, **kwargs)

    return decorated_function


def api_rate_limit(max_requests: int = 100, window: int = 3600):
    """Simple rate limiting decorator for API endpoints."""
    requests_cache = {}

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.remote_addr
            current_time = datetime.utcnow().timestamp()

            if ip_address not in requests_cache:
                requests_cache[ip_address] = []

            requests_cache[ip_address] = [
                t for t in requests_cache[ip_address] if current_time - t < window
            ]

            if len(requests_cache[ip_address]) >= max_requests:
                return jsonify(
                    {"error": "Rate limit exceeded", "code": "RATE_LIMIT"}
                ), 429

            requests_cache[ip_address].append(current_time)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_api_request(endpoint: str) -> None:
    """Log API requests for monitoring."""
    username = (
        request.api_user.get("username", "Anonymous")
        if hasattr(request, "api_user")
        else "Unauthenticated"
    )
    ip_address = request.remote_addr
    api_logger.info(f"API: {username} | {request.method} {endpoint} | IP: {ip_address}")


def success_response(data: Any, pagination: Optional[dict] = None) -> tuple:
    """Create standardized success response."""
    response = {"success": True, "data": data}
    if pagination:
        response["pagination"] = pagination
    return jsonify(response), 200


def error_response(error: str, code: str, status: int = 400) -> tuple:
    """Create standardized error response."""
    return jsonify({"success": False, "error": error, "code": code}), status


@api.route("/auth/login", methods=["POST"])
@api_rate_limit(max_requests=10, window=300)
def api_login():
    """Authenticate and return JWT token."""
    data = request.get_json()

    if not data:
        return error_response("Request body required", "NO_DATA", 400)

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return error_response(
            "Username and password required", "MISSING_CREDENTIALS", 400
        )

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password) or not user.is_active:
        return error_response("Invalid credentials", "INVALID_CREDENTIALS", 401)

    token = create_token(user.user_id, user.username, user.role)

    return success_response(
        {
            "token": token,
            "user": {"id": user.user_id, "username": user.username, "role": user.role},
            "expires_in": Config.JWT_ACCESS_TOKEN_EXPIRES,
        }
    )


@api.route("/auth/refresh", methods=["POST"])
@jwt_required
def refresh_token():
    """Refresh JWT token."""
    payload = request.api_user
    user = db.session.get(User, payload["user_id"])

    if not user or not user.is_active:
        return error_response("User not found or inactive", "USER_INACTIVE", 401)

    token = create_token(user.user_id, user.username, user.role)

    return success_response(
        {"token": token, "expires_in": Config.JWT_ACCESS_TOKEN_EXPIRES}
    )


@api.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        db.session.execute(db.text("SELECT 1"))
        return success_response(
            {"status": "healthy", "database": "connected", "version": "1.0.0"}
        )
    except Exception as e:
        return error_response(str(e), "DB_ERROR", 503)


@api.route("/products", methods=["GET"])
@jwt_required
@api_rate_limit()
def get_products():
    """Get all active products with pagination."""
    log_api_request("/products")

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    search = request.args.get("search", "").strip()
    product_type = request.args.get("type", "").strip()
    low_stock = request.args.get("low_stock", "").lower() == "true"

    query = Product.query.filter_by(is_active=True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.product_name.ilike(search_term),
                Product.product_model.ilike(search_term),
                Product.product_type.ilike(search_term),
            )
        )

    if product_type:
        query = query.filter_by(product_type=product_type)

    if low_stock:
        query = query.filter(Product.product_quantity <= Product.low_stock_threshold)

    pagination = query.order_by(Product.product_name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response(
        [
            {
                "id": p.product_id,
                "name": p.product_name,
                "type": p.product_type,
                "model": p.product_model,
                "color": p.product_color,
                "price": float(p.product_price),
                "quantity": p.product_quantity,
                "low_stock_threshold": p.low_stock_threshold,
                "is_low_stock": p.is_low_stock,
            }
            for p in pagination.items
        ],
        pagination={
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    )


@api.route("/products/<int:product_id>", methods=["GET"])
@jwt_required
def get_product(product_id):
    """Get a single product by ID."""
    log_api_request(f"/products/{product_id}")
    product = Product.query.get_or_404(product_id)

    return success_response(
        {
            "id": product.product_id,
            "name": product.product_name,
            "type": product.product_type,
            "model": product.product_model,
            "color": product.product_color,
            "price": float(product.product_price),
            "quantity": product.product_quantity,
            "low_stock_threshold": product.low_stock_threshold,
            "is_low_stock": product.is_low_stock,
            "created_at": product.created_at.isoformat()
            if product.created_at
            else None,
        }
    )


@api.route("/customers", methods=["GET"])
@jwt_required
@api_rate_limit()
def get_customers():
    """Get all active customers with pagination."""
    log_api_request("/customers")

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    search = request.args.get("search", "").strip()

    query = Customer.query.filter_by(is_active=True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Customer.first_name.ilike(search_term),
                Customer.last_name.ilike(search_term),
                Customer.phone_number.ilike(search_term),
                Customer.email.ilike(search_term),
            )
        )

    pagination = query.order_by(Customer.first_name, Customer.last_name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response(
        [
            {
                "id": c.customer_id,
                "name": c.full_name,
                "phone": c.phone_number,
                "email": c.email,
                "address": c.customer_address,
            }
            for c in pagination.items
        ],
        pagination={
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    )


@api.route("/customers/<int:customer_id>", methods=["GET"])
@jwt_required
def get_customer(customer_id):
    """Get a single customer by ID."""
    log_api_request(f"/customers/{customer_id}")
    customer = Customer.query.get_or_404(customer_id)

    return success_response(
        {
            "id": customer.customer_id,
            "name": customer.full_name,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "phone": customer.phone_number,
            "email": customer.email,
            "address": customer.customer_address,
            "created_at": customer.created_at.isoformat()
            if customer.created_at
            else None,
        }
    )


@api.route("/invoices", methods=["GET"])
@jwt_required
@api_rate_limit()
def get_invoices():
    """Get invoices with optional filters and pagination."""
    log_api_request("/invoices")

    status = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    query = Invoice.query

    if status != "all":
        query = query.filter_by(status=status)

    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response(
        [
            {
                "id": inv.invoice_id,
                "number": inv.invoice_number,
                "customer": inv.customer.full_name if inv.customer else "Unknown",
                "status": inv.status,
                "total": float(inv.total),
                "subtotal": float(inv.subtotal),
                "tax_amount": float(inv.tax_amount),
                "discount_amount": float(inv.discount_amount),
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
            }
            for inv in pagination.items
        ],
        pagination={
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    )


@api.route("/invoices/<int:invoice_id>", methods=["GET"])
@jwt_required
def get_invoice(invoice_id):
    """Get a single invoice with items."""
    log_api_request(f"/invoices/{invoice_id}")
    invoice = Invoice.query.get_or_404(invoice_id)

    return success_response(
        {
            "id": invoice.invoice_id,
            "number": invoice.invoice_number,
            "customer": invoice.customer.full_name if invoice.customer else "Unknown",
            "customer_id": invoice.customer_details,
            "status": invoice.status,
            "subtotal": float(invoice.subtotal),
            "tax_rate": float(invoice.tax_rate),
            "tax_amount": float(invoice.tax_amount),
            "discount_amount": float(invoice.discount_amount),
            "total": float(invoice.total),
            "payment_method": invoice.payment_method,
            "payment_date": invoice.payment_date.isoformat()
            if invoice.payment_date
            else None,
            "notes": invoice.notes,
            "created_at": invoice.created_at.isoformat()
            if invoice.created_at
            else None,
            "items": [
                {
                    "id": item.item_id,
                    "product_name": item.product.product_name
                    if item.product
                    else "Unknown",
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "discount_amount": float(item.discount_amount),
                    "total": float(item.total),
                }
                for item in invoice.items
            ],
        }
    )


@api.route("/stock", methods=["GET"])
@jwt_required
@api_rate_limit()
def get_stock():
    """Get stock levels for all products with pagination."""
    log_api_request("/stock")

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 100)

    pagination = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.product_quantity.asc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    products_list = [
        {
            "id": p.product_id,
            "name": p.product_name,
            "quantity": p.product_quantity,
            "threshold": p.low_stock_threshold,
            "is_low_stock": p.is_low_stock,
        }
        for p in pagination.items
    ]

    low_stock_count = Product.query.filter(
        Product.is_active == True,
        Product.product_quantity <= Product.low_stock_threshold,
    ).count()

    out_of_stock_count = Product.query.filter(
        Product.is_active == True, Product.product_quantity == 0
    ).count()

    return success_response(
        products_list,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    )


@api.route("/stock/movements", methods=["GET"])
@jwt_required
@api_rate_limit()
def get_stock_movements():
    """Get stock movement history with pagination."""
    log_api_request("/stock/movements")

    product_id = request.args.get("product_id", type=int)
    movement_type = request.args.get("type", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 100)

    query = StockMovement.query

    if product_id:
        query = query.filter_by(product_id=product_id)
    if movement_type:
        query = query.filter_by(movement_type=movement_type)

    pagination = query.order_by(StockMovement.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success_response(
        [
            {
                "id": m.movement_id,
                "product_name": m.product.product_name if m.product else "Unknown",
                "type": m.movement_type,
                "quantity": m.quantity,
                "reference_type": m.reference_type,
                "reference_id": m.reference_id,
                "notes": m.notes,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in pagination.items
        ],
        pagination={
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    )


@api.route("/dashboard", methods=["GET"])
@jwt_required
@api_rate_limit()
def get_dashboard():
    """Get dashboard statistics."""
    log_api_request("/dashboard")

    total_customers = Customer.query.filter_by(is_active=True).count()
    total_products = Product.query.filter_by(is_active=True).count()
    total_invoices = Invoice.query.count()
    pending_invoices = Invoice.query.filter_by(status="pending").count()
    paid_invoices = Invoice.query.filter_by(status="paid").count()
    total_revenue = (
        db.session.query(db.func.sum(Invoice.total))
        .filter(Invoice.status == "paid")
        .scalar()
        or 0
    )

    low_stock_products = Product.query.filter(
        Product.product_quantity <= Product.low_stock_threshold,
        Product.is_active == True,
    ).count()

    return success_response(
        {
            "stats": {
                "customers": total_customers,
                "products": total_products,
                "invoices": total_invoices,
                "pending_invoices": pending_invoices,
                "paid_invoices": paid_invoices,
                "total_revenue": float(total_revenue),
                "low_stock_alerts": low_stock_products,
            }
        }
    )


@api.route("/swagger", methods=["GET"])
def swagger_ui():
    """Serve Swagger UI."""
    return render_template_string(SWAGGER_UI_HTML)


@api.route("/openapi.json", methods=["GET"])
def openapi_spec():
    """Serve OpenAPI specification."""
    return jsonify(OPENAPI_SPEC)


@api.route("/docs", methods=["GET"])
def api_docs():
    """Return API documentation."""
    return success_response(
        {
            "title": "POS Application API",
            "version": "1.0.0",
            "authentication": "Bearer token required for all endpoints except /health and /auth/login",
            "endpoints": {
                "health": "GET /api/v1/health - Health check (public)",
                "auth_login": "POST /api/v1/auth/login - Get JWT token",
                "auth_refresh": "POST /api/v1/auth/refresh - Refresh JWT token",
                "products": "GET /api/v1/products - List products (supports ?search=, ?type=, ?low_stock=, ?page=, ?per_page=)",
                "product_detail": "GET /api/v1/products/<id> - Get product details",
                "customers": "GET /api/v1/customers - List customers (supports ?search=, ?page=, ?per_page=)",
                "customer_detail": "GET /api/v1/customers/<id> - Get customer details",
                "invoices": "GET /api/v1/invoices - List invoices (supports ?status=, ?page=, ?per_page=)",
                "invoice_detail": "GET /api/v1/invoices/<id> - Get invoice with items",
                "stock": "GET /api/v1/stock - Get stock levels (supports ?page=, ?per_page=)",
                "stock_movements": "GET /api/v1/stock/movements - Get movement history (supports ?product_id=, ?type=, ?page=, ?per_page=)",
                "dashboard": "GET /api/v1/dashboard - Get dashboard stats",
            },
        }
    )


@api.errorhandler(404)
def not_found(e):
    return error_response("Resource not found", "NOT_FOUND", 404)


@api.errorhandler(500)
def server_error(e):
    return error_response("Internal server error", "SERVER_ERROR", 500)
