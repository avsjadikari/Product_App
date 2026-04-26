# AGENTS.md - Agent Coding Guidelines

This file provides guidance for AI agents working in this repository.

## Project Overview

A Flask web application for managing customers, products, invoices with shopping cart functionality. Uses Flask-SQLAlchemy with PostgreSQL. Includes authentication, role-based access control, comprehensive audit logging, stock management, reporting features, REST API with JWT authentication, Swagger/OpenAPI documentation, Docker deployment support, and database setup wizard.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Web Framework | Flask 3.x |
| ORM | Flask-SQLAlchemy |
| Database | PostgreSQL |
| Forms | Flask-WTF |
| Authentication | Werkzeug (password hashing) |
| API Auth | JWT (PyJWT) |
| Migrations | Flask-Migrate |
| UI | Bootstrap 5 + Jinja2 |
| API Documentation | Swagger UI (OpenAPI 3.0) |
| Production Server | Gunicorn |
| Containerization | Docker, Docker Compose |
| Testing | pytest |

## Running the Application

### Installation

```bash
pip install -r requirements.txt
```

### First Run (Setup Wizard)

On first run, the application redirects to `/setup` for database configuration:

1. Enter PostgreSQL connection details (host, port, database, username, password)
2. Enter application secret key
3. Test connection
4. Save and continue to login

### Development Server

```bash
python app.py
```

Runs on http://localhost:5000. Debug mode controlled by `FLASK_DEBUG` or `DEBUG` environment variable.

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Production with Gunicorn

```bash
gunicorn -c gunicorn.conf.py app:app
# Or
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=product

# Application
SECRET_KEY=your-secret-key-change-in-production
FLASK_DEBUG=True
FLASK_ENV=development

# Optional Settings
DEFAULT_TAX_RATE=0
ITEMS_PER_PAGE=20
LOG_LEVEL=INFO

# Security (change on first login)
DEFAULT_ADMIN_USER=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_USER_USER=user
DEFAULT_USER_PASSWORD=user123

# Rate Limiting
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW=300

# Password Requirements
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
```

### Database

- PostgreSQL at localhost:5432
- Database name: `product`
- Credentials via environment variables or setup wizard
- Tables auto-created on startup (or via Liquibase)
- Use Flask-Migrate for schema changes

### Sample Data

Auto-loaded when database is empty:
- 2 users: admin (password: admin123), user (password: user123)
- 3 customers: John Doe, Jane Smith, Bob Johnson
- 5 products: ThinkPad, iPhone 14 Pro, iPad Air, Dell Monitor, Logitech Keyboard

### Resetting Database

```bash
curl -X POST http://localhost:5000/database/reset
```

Requires admin authentication. Clears all data and recreates sample data.

## Routes

### Authentication
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/login` | GET, POST | User login (with CSRF) |
| `/logout` | GET | User logout |
| `/profile/change-password` | GET, POST | Change password (requires login) |
| `/setup` | GET, POST | Database setup wizard (first run) |
| `/setup/test-connection` | POST | Test database connection |

### Dashboard
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/` | GET | Dashboard with stats, charts, low stock alerts |

### User Management (Admin only)
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/users` | GET | List all users |
| `/users/add` | POST | Create new user |
| `/users/delete/<int:id>` | GET | Deactivate user |

### Audit Logs (Admin only)
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/audit-logs` | GET | View all user activities with filters |

### Customer Management
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/customers` | GET | List customers with search/pagination |
| `/customers/add` | POST | Add new customer |
| `/customers/edit/<int:id>` | GET, POST | Edit customer |
| `/customers/view/<int:id>` | GET | View customer profile with invoices |
| `/customers/delete/<int:id>` | GET | Soft delete customer |

### Product Management
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/products` | GET | List products with search/filter/pagination |
| `/products/add` | POST | Add new product |
| `/products/edit/<int:id>` | GET, POST | Edit product |
| `/products/delete/<int:id>` | GET | Soft delete product |

### Stock Management
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/stock` | GET | View stock levels and movement history |
| `/stock/adjust` | POST | Adjust stock quantities |

### Cart & Checkout
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/cart` | GET | View cart |
| `/cart/add/<int:id>` | POST | Add product to cart |
| `/cart/remove/<int:id>` | GET | Remove item from cart |
| `/cart/update/<int:id>` | POST | Update item quantity |
| `/cart/clear` | GET | Clear cart |
| `/cart/checkout` | POST | Create invoice from cart |

### Invoice Management
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/invoices` | GET | List invoices with filters/pagination |
| `/invoices/create` | POST | Create new invoice |
| `/invoices/edit/<int:id>` | GET, POST | Edit invoice (draft/pending only) |
| `/invoices/add-item/<int:id>` | POST | Add item to invoice |
| `/invoices/remove-item/<int:id>` | GET | Remove item from invoice |
| `/invoices/update-status/<int:id>` | POST | Update invoice status |
| `/invoices/delete/<int:id>` | GET | Delete invoice (draft/pending only) |
| `/invoice/print/<int:id>` | GET | Print invoice |

### Reports
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/reports/sales` | GET | Sales report with date filters |
| `/reports/stock` | GET | Stock report with value calculations |

### Exports
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/export/products` | GET | Export products to CSV |
| `/export/customers` | GET | Export customers to CSV |
| `/export/invoices` | GET | Export invoices to CSV |
| `/export/sales-report` | GET | Export sales report to CSV |

### AJAX Search
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/search/products` | GET | AJAX product search |
| `/search/customers` | GET | AJAX customer search |

### Utilities
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/database/reset` | POST | Reset database to defaults (admin only) |

### Error Pages
| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/404` | GET | Custom 404 error page |
| `/500` | GET | Custom 500 error page |

### API Endpoints
| Endpoint | Methods | Auth | Description |
|----------|---------|------|-------------|
| `/api/v1/health` | GET | No | Health check |
| `/api/v1/swagger` | GET | No | Swagger UI |
| `/api/v1/openapi.json` | GET | No | OpenAPI specification |
| `/api/v1/docs` | GET | No | API documentation (JSON) |
| `/api/v1/auth/login` | POST | No | Get JWT token |
| `/api/v1/auth/refresh` | POST | JWT | Refresh JWT token |
| `/api/v1/products` | GET | JWT | List products (paginated) |
| `/api/v1/products/<int:id>` | GET | JWT | Get product |
| `/api/v1/customers` | GET | JWT | List customers |
| `/api/v1/customers/<int:id>` | GET | JWT | Get customer |
| `/api/v1/invoices` | GET | JWT | List invoices |
| `/api/v1/invoices/<int:id>` | GET | JWT | Get invoice |
| `/api/v1/stock` | GET | JWT | Stock levels |
| `/api/v1/stock/movements` | GET | JWT | Movement history |
| `/api/v1/dashboard` | GET | JWT | Dashboard stats |

## User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access including user management, audit logs, database reset |
| `user` | Customer, product, invoice, cart, reports management |

## Audit Logging

### Overview

All user actions are logged to `logs/app.log` with:
- Username
- Action type
- IP address
- Timestamp
- Additional details

### Tracked Actions

| Action Type | Description |
|-------------|-------------|
| LOGIN | User logged in successfully |
| LOGOUT | User logged out |
| LOGIN_FAILED | Failed login attempt |
| USER_CREATE | Created new user |
| USER_DELETE | Deactivated user |
| CUSTOMER_CREATE | Created new customer |
| CUSTOMER_UPDATE | Updated customer |
| CUSTOMER_DELETE | Deleted customer |
| PRODUCT_CREATE | Created new product |
| PRODUCT_UPDATE | Updated product |
| PRODUCT_DELETE | Deleted product |
| STOCK_IN | Manual stock increase |
| STOCK_OUT | Manual stock decrease |
| CART_ADD | Added item to cart |
| CART_UPDATE | Updated cart quantity |
| CART_REMOVE | Removed item from cart |
| INVOICE_CREATE | Created new invoice |
| INVOICE_PAID | Marked invoice as paid |
| INVOICE_PENDING | Changed invoice to pending |
| INVOICE_CANCELLED | Cancelled invoice |
| INVOICE_DELETE | Deleted invoice |
| EXPORT | Exported data to CSV |

### Audit Log Viewer

Admin users can access `/audit-logs` to view:
- All activities with filters
- Date range filter (Today, 7 days, 30 days, All Time)
- Action type filter
- User filter

## Security Features

- **Password Hashing**: Uses Werkzeug's PBKDF2+SHA256
- **Session Management**: Flask session with secure cookie
- **CSRF Protection**: Flask-WTF tokens on all forms
- **Authentication**: `@login_required` decorator
- **Authorization**: `@admin_required` decorator for admin-only routes
- **Rate Limiting**: IP-based rate limiting on login
- **Input Sanitization**: Search inputs limited to configurable length
- **Transaction Rollback**: Database operations wrapped in try/except with rollback
- **Audit Logging**: Comprehensive user action logging with username, IP, and timestamp
- **JWT Authentication**: Token-based auth for API endpoints
- **Password Validation**: Configurable requirements (length, uppercase, lowercase, digits, special chars)
- **Custom Error Pages**: Branded 404 and 500 pages

## Code Style Guidelines

### General Principles
- Keep functions small and focused (single responsibility)
- Use meaningful variable and function names
- Avoid code duplication; use helper functions
- Handle errors gracefully with appropriate flash messages

### Imports
Order: standard library → flask → flask_sqlalchemy → other third-party → local modules

```python
import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from models import db, Customer, Product, Invoice, InvoiceItem
from config import Config
from forms import CustomerForm, ProductForm
```

### Formatting
- Maximum line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Use blank lines to separate logical sections
- Add docstrings to complex functions

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Files | lowercase with underscores | `app.py`, `models.py` |
| Classes | PascalCase | `Customer`, `InvoiceItem` |
| Functions/variables | snake_case | `get_cart()`, `cart_items` |
| Constants | UPPER_SNAKE_CASE | `MAX_SEARCH_LENGTH` |
| Database tables | singular, lowercase | `customer`, `product` |

### SQLAlchemy Models
- Use `db.Model` as base class
- Define `__tablename__` explicitly (singular form)
- Use `db.Column` with explicit types
- Use `NUMERIC(10,2)` for money fields (not Float)
- Define foreign keys with `db.ForeignKey("table.column")`
- Use `db.relationship()` with `back_populates` for bidirectional relationships
- Add indexes for frequently queried columns using `__table_args__`
- Always include `is_active` flag for soft delete

### Routes
- Use decorator `@app.route()` with explicit methods
- Validate form inputs before processing
- Use flash messages for user feedback (success/danger/warning/info)
- Always redirect after POST requests (post-redirect-get pattern)
- Use `@login_required` for protected routes
- Use `@admin_required` for admin-only routes

### Error Handling
- Use `get_or_404()` for resource not found cases
- Validate stock availability before cart operations
- Check for empty cart before checkout
- Use try/except with rollback for database operations
- Log errors with `log_error()` helper

### Templates (Jinja2)
- Store in `templates/` directory
- Use Bootstrap 5 for responsive UI
- Use `url_for()` for all internal links
- Pass flash messages via `get_flashed_messages()` loop
- Include `{{ form.hidden_tag() }}` for CSRF protection in forms

### Currency
- All prices use NUMERIC(10,2) in database
- Display as LKR format with 2 decimal places

### Database Operations
- Use `db.session.add()` for new records
- Call `db.session.commit()` after modifications
- Use `db.session.flush()` to get auto-generated IDs
- Use `joinedload()` for eager loading relationships
- Wrap multi-step operations in try/except with `db.session.rollback()`

### Cart Implementation
- Session-based cart using `session['cart']`
- Cart is list of dicts: `[{'product_id': int, 'quantity': int}]`
- Always validate stock before adding/updating cart items
- Clear cart after successful checkout
- Use transaction rollback on checkout failure

### Audit Logging
- Use `log_user_action(action, details)` for all user actions
- Include relevant details (names, quantities, amounts)
- Actions are logged to `logs/app.log`
- Admin can view via `/audit-logs`

## Helper Functions

| Function | Description |
|----------|-------------|
| `get_current_user()` | Returns current User object from session |
| `sanitize_search_input(term)` | Sanitizes search input with max length |
| `check_rate_limit(ip)` | Checks if IP has exceeded login attempts |
| `get_cart()` | Returns cart from session |
| `save_cart(cart)` | Saves cart to session |
| `update_stock(...)` | Updates product quantity with rollback |
| `record_stock_movement(...)` | Records stock movement with rollback |
| `log_user_action(action, details)` | Logs user action for audit trail |
| `log_error(type, message)` | Logs error for monitoring |
| `validate_password(password)` | Validates password meets requirements |
| `safe_int_convert(value, default)` | Safely convert to int |
| `safe_float_convert(value, default)` | Safely convert to float |

## Testing

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run all tests
pytest

# Run a single test file
pytest tests/test_models.py -v

# Run specific test
pytest tests/test_file.py::test_function_name -v
```

### Test Files

| File | Description |
|------|-------------|
| `tests/conftest.py` | Pytest fixtures and configuration |
| `tests/test_models.py` | Model unit tests |
| `tests/test_forms.py` | Form validation tests |
| `tests/test_routes.py` | Route/integration tests |
| `tests/test_api.py` | API endpoint tests |

## Key Files

| File | Description |
|------|-------------|
| `app.py` | Flask application with all routes, helpers, and configuration |
| `models.py` | SQLAlchemy ORM models (User, Customer, Product, Invoice, InvoiceItem, StockMovement) |
| `forms.py` | WTForms with validation |
| `utils.py` | CSV export functions, search helpers, formatting utilities |
| `config.py` | Configuration class with environment variable and file support |
| `api.py` | REST API blueprint with JWT authentication and Swagger documentation |
| `templates/` | Jinja2 HTML templates |
| `liquibase/` | Database migration XML files |
| `tests/` | Test suite |
| `Dockerfile` | Docker build configuration |
| `docker-compose.yml` | Docker Compose configuration |
| `gunicorn.conf.py` | Gunicorn production server configuration |
| `Procfile` | Deployment configuration for Heroku/Render |

## Configuration

### Config Class (config.py)

The `Config` class provides centralized configuration:

```python
# Database (via .env or config.json)
DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Application
SECRET_KEY, FLASK_DEBUG, FLASK_ENV
DEFAULT_TAX_RATE, ITEMS_PER_PAGE
LOG_LEVEL, LOG_FILE

# Security
DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASSWORD
DEFAULT_USER_USER, DEFAULT_USER_PASSWORD
PASSWORD_MIN_LENGTH, PASSWORD_REQUIRE_*
LOGIN_RATE_LIMIT, LOGIN_RATE_WINDOW

# JWT
JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES
```

### Database Setup Methods

1. **Setup Wizard** (Recommended): First run redirects to `/setup`
2. **Environment Variables**: Create `.env` file
3. **Docker Compose**: Use docker-compose.yml
4. **Liquibase**: Use `liquibase/master.xml` for external migrations

## Docker Support

### Quick Start

```bash
# Build and run
docker-compose up --build

# Access application at http://localhost:5000
```

### Environment Variables for Docker

```env
DB_PASSWORD=postgres
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

## Security Notes

- Default credentials should be changed on first login (users are forced to change password)
- SECRET_KEY should be changed in production
- DEBUG should be False in production
- Rate limiting prevents brute-force attacks
- Input sanitization prevents abuse
- All passwords are hashed using Werkzeug
- Soft delete preserves data integrity
- Comprehensive audit logging tracks all user actions
- Use NUMERIC for money fields (not Float)

## Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Make changes** following code style guidelines
3. **Test locally**: `python app.py`
4. **Run linting**: `python -m py_compile app.py`
5. **Run tests**: `pytest`
6. **Commit changes**: `git add . && git commit -m "Description"`
7. **Push to remote**: `git push origin feature/your-feature`

## Liquibase (External Database)

```bash
# Create database
createdb product

# Run migrations
liquibase --url="jdbc:postgresql://localhost:5432/product" \
           --username=postgres \
           --password=yourpass \
           --changelog-file=liquibase/master.xml \
           update
```