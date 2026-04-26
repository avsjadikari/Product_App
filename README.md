# Product App - Point of Sale Management System

A Flask-based Point of Sale (POS) application for managing customers, products, invoices, and inventory. Features include shopping cart, invoice generation, stock tracking, sales reporting, REST API with Swagger documentation, and comprehensive audit logging.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Setup Methods](#setup-methods)
- [Running the Application](#running-the-application)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Default Credentials](#default-credentials)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Audit Logging](#audit-logging)
- [Project Structure](#project-structure)
- [Security Features](#security-features)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Features

- **User Management**: Role-based access control (Admin/User)
- **Customer Management**: Add, edit, view, soft-delete customers
- **Product Management**: Product inventory with categories, pricing, stock levels
- **Shopping Cart**: Session-based cart with stock validation
- **Invoice Management**: Create, edit, print invoices with tax/discount
- **Stock Management**: Automatic stock tracking with movement history
- **Reports**: Sales reports and stock valuation reports
- **CSV Export**: Export products, customers, invoices to CSV
- **REST API**: JWT-authenticated API with Swagger UI documentation
- **API Documentation**: Interactive Swagger UI at `/api/v1/swagger`
- **Audit Logging**: Comprehensive audit trail of all user actions
- **Audit Log Viewer**: Admin-only web interface to view all activities
- **Custom Error Pages**: Branded 404 and 500 error pages
- **Docker Support**: Containerized deployment with Docker Compose
- **Production Ready**: Gunicorn configuration for production deployment
- **Database Setup Wizard**: First-time setup via web interface

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Web Framework | Flask 3.x |
| ORM | Flask-SQLAlchemy |
| Database | PostgreSQL |
| Forms | Flask-WTF |
| Authentication | Werkzeug (password hashing) |
| API Auth | JWT (PyJWT) |
| Database Migrations | Flask-Migrate |
| UI | Bootstrap 5 + Jinja2 |
| API Documentation | Swagger UI (OpenAPI 3.0) |
| Production Server | Gunicorn |
| Containerization | Docker, Docker Compose |
| Testing | pytest |

---

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip package manager
- Docker (optional, for containerized deployment)

---

## Quick Start

```bash
# 1. Clone or download the project
cd Product_App

# 2. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py

# 5. Open browser to http://localhost:5000
# Follow the setup wizard to configure database
```

---

## Setup Methods

### Method 1: Setup Wizard (Recommended)

1. Run the application: `python app.py`
2. Open browser to `http://localhost:5000`
3. You will be redirected to `/setup`
4. Enter database connection details:
   - **Host**: Your PostgreSQL server (e.g., `localhost`)
   - **Port**: PostgreSQL port (default: `5432`)
   - **Database Name**: Name of database to create/use
   - **Username**: PostgreSQL username
   - **Password**: PostgreSQL password
   - **Secret Key**: Application secret key for sessions
5. Click **Test Connection** to verify
6. Click **Save & Continue**
7. Login with default credentials

### Method 2: Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=product

# Application Settings
SECRET_KEY=your-secure-secret-key-change-in-production
FLASK_DEBUG=True
FLASK_ENV=development

# Optional Settings
DEFAULT_TAX_RATE=0
ITEMS_PER_PAGE=20
LOG_LEVEL=INFO

# Default Users (change on first login)
DEFAULT_ADMIN_USER=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_USER_USER=user
DEFAULT_USER_PASSWORD=user123

# Security Settings
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=true
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW=300

# JWT Settings (for API)
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
```

Then run: `python app.py`

### Method 3: Docker Deployment

```bash
# 1. Copy the example environment file
copy .env.example .env

# 2. Edit .env with your preferences (DB_PASSWORD is required)

# 3. Build and start containers
docker-compose up --build

# 4. Open browser to http://localhost:5000
```

### Method 4: Liquibase (External Database)

For production or external database management:

```bash
# 1. Create the database
createdb product

# 2. Install Liquibase (if not installed)
# Download from: https://www.liquibase.org/download

# 3. Run migrations
liquibase --url="jdbc:postgresql://localhost:5432/product" \
           --username=postgres \
           --password=your_password \
           --changelog-file=liquibase/master.xml \
           update

# 4. Manually insert default users (or use database reset feature)
```

---

## Running the Application

### Development
```bash
python app.py
```
Runs on `http://localhost:5000` with debug mode enabled.

### Production
```bash
# Set environment variables
export FLASK_DEBUG=False
export FLASK_ENV=production

# Run with production server
python app.py
```

### Using Gunicorn (Recommended for Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or use the included configuration:
```bash
gunicorn -c gunicorn.conf.py app:app
```

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services

| Service | Description | Port |
|---------|-------------|------|
| app | Flask application | 5000 |
| db | PostgreSQL database | 5432 |

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
DB_PASSWORD=your_password
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

### Manual Docker Build

```bash
# Build the image
docker build -t product-app .

# Run the container
docker run -d -p 5000:5000 \
  -e DB_HOST=db \
  -e DB_NAME=productapp \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  --link postgres:db \
  product-app
```

---

## Production Deployment

### Using Gunicorn with Configuration File

```bash
# The gunicorn.conf.py is already configured
gunicorn app:app

# Or specify custom settings
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
```

### Using Procfile (for Heroku, Render, etc.)

The `Procfile` is configured for deployment platforms:

```
web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 app:app
```

### Production Checklist

1. Set `FLASK_ENV=production`
2. Set `FLASK_DEBUG=False`
3. Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
4. Use PostgreSQL (not SQLite)
5. Enable HTTPS/SSL
6. Configure proper CORS if needed
7. Set up log rotation (included in gunicorn.conf.py)

---

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| User | `user` | `user123` |

> **Important**: On first login, users will be prompted to change their password.

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | localhost | PostgreSQL host |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_NAME` | product | Database name |
| `DB_USER` | postgres | Database username |
| `DB_PASSWORD` | - | Database password |
| `SECRET_KEY` | dev-secret-key... | Flask session secret |
| `FLASK_DEBUG` | False | Enable debug mode |
| `FLASK_ENV` | development | Environment |
| `DEFAULT_TAX_RATE` | 0 | Default tax percentage |
| `ITEMS_PER_PAGE` | 20 | Pagination size |
| `LOG_LEVEL` | INFO | Logging level |
| `JWT_SECRET_KEY` | jwt-secret... | JWT signing key |
| `JWT_ACCESS_TOKEN_EXPIRES` | 3600 | Token expiry (seconds) |
| `PASSWORD_MIN_LENGTH` | 8 | Minimum password length |
| `PASSWORD_REQUIRE_UPPERCASE` | true | Require uppercase |
| `PASSWORD_REQUIRE_LOWERCASE` | true | Require lowercase |
| `PASSWORD_REQUIRE_DIGIT` | true | Require digit |
| `PASSWORD_REQUIRE_SPECIAL` | true | Require special char |
| `LOGIN_RATE_LIMIT` | 5 | Max login attempts |
| `LOGIN_RATE_WINDOW` | 300 | Rate limit window (seconds) |

---

## API Documentation

### Interactive Swagger UI

Access the interactive API documentation at: `http://localhost:5000/api/v1/swagger`

### OpenAPI Specification

The full OpenAPI 3.0 specification is available at: `http://localhost:5000/api/v1/openapi.json`

### Authentication

```bash
# Login to get JWT token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response
{
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {"id": 1, "username": "admin", "role": "admin"},
    "expires_in": 3600
  },
  "success": true
}
```

### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/health` | No | Health check |
| GET | `/api/v1/swagger` | No | Swagger UI |
| GET | `/api/v1/openapi.json` | No | OpenAPI spec |
| POST | `/api/v1/auth/login` | No | Get JWT token |
| POST | `/api/v1/auth/refresh` | JWT | Refresh token |
| GET | `/api/v1/products` | JWT | List products |
| GET | `/api/v1/products/<id>` | JWT | Get product |
| GET | `/api/v1/customers` | JWT | List customers |
| GET | `/api/v1/customers/<id>` | JWT | Get customer |
| GET | `/api/v1/invoices` | JWT | List invoices |
| GET | `/api/v1/invoices/<id>` | JWT | Get invoice |
| GET | `/api/v1/stock` | JWT | Stock levels |
| GET | `/api/v1/stock/movements` | JWT | Movement history |
| GET | `/api/v1/dashboard` | JWT | Dashboard stats |

### Using the API

```bash
# Set token variable
TOKEN="your-jwt-token"

# Get products
curl http://localhost:5000/api/v1/products \
  -H "Authorization: Bearer $TOKEN"

# With pagination
curl "http://localhost:5000/api/v1/products?page=1&per_page=20" \
  -H "Authorization: Bearer $TOKEN"

# With search
curl "http://localhost:5000/api/v1/products?search=laptop" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Audit Logging

### Overview

All user actions are automatically logged to `logs/app.log` with:
- Username
- Action type
- IP address
- Timestamp
- Additional details

### Audit Log Viewer

Admin users can view audit logs via the web interface at `/audit-logs`

Features:
- Filter by date range (Today, 7 days, 30 days, All)
- Filter by action type
- Filter by username

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

---

## Project Structure

```
Product_App/
├── app.py                  # Main Flask application
├── models.py               # SQLAlchemy ORM models
├── forms.py               # WTForms
├── config.py              # Configuration management
├── api.py                 # REST API blueprint with Swagger
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── pytest.ini            # Pytest configuration
├── Dockerfile            # Docker build configuration
├── docker-compose.yml    # Docker Compose configuration
├── Procfile              # Deployment configuration (Heroku)
├── gunicorn.conf.py      # Gunicorn configuration
├── .dockerignore        # Docker ignore file
├── .env.example         # Example environment variables
│
├── templates/            # Jinja2 templates
│   ├── base.html        # Base template
│   ├── login.html       # Login page
│   ├── setup.html       # Database setup wizard
│   ├── home.html        # Dashboard
│   ├── 404.html         # Custom 404 error page
│   ├── 500.html         # Custom 500 error page
│   ├── audit_logs.html  # Audit log viewer (Admin)
│   └── ...
│
├── tests/               # Test suite
│   ├── conftest.py     # Pytest fixtures
│   ├── test_models.py
│   ├── test_forms.py
│   ├── test_routes.py
│   └── test_api.py
│
├── liquibase/           # Database migrations
│   ├── master.xml
│   └── changelogs/
│       ├── 001-users.xml
│       ├── 002-customers.xml
│       ├── 003-products.xml
│       ├── 004-stock-movements.xml
│       ├── 005-invoices.xml
│       └── 006-invoice-items.xml
│
├── logs/                # Application logs
│   └── app.log          # Audit and application logs
│
└── config.json          # Runtime config (auto-generated)
```

---

## Security Features

- **Password Hashing**: Werkzeug's PBKDF2+SHA256
- **Session Security**: Secure, HTTP-only cookies
- **CSRF Protection**: Flask-WTF CSRFProtect on all POST forms (including AJAX)
- **Rate Limiting**: IP-based login protection
- **Input Validation**: Type checking and sanitization
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy ORM + input validation
- **JWT Authentication**: Token-based API security
- **Audit Logging**: Comprehensive user action logging
- **Decimal Precision**: NUMERIC(10,2) for money fields to prevent floating-point errors
- **Custom Error Pages**: Branded 404 and 500 pages

---

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Style

- Follows PEP 8 guidelines
- Maximum line length: 100 characters
- Type hints on functions
- Docstrings on complex functions

### Database Migrations

```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
```

---

## Troubleshooting

### Database Connection Failed

1. Check PostgreSQL is running: `pg_isready`
2. Verify credentials in `.env` or setup wizard
3. Ensure database exists: `createdb product`
4. Check firewall allows port 5432

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Session Issues

```bash
# Clear browser cookies
# Or delete config.json to re-run setup wizard
```

### Port Already in Use

```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process
taskkill /PID <PID> /F

# Or use different port
set FLASK_PORT=5001
python app.py
```

### Reset Database

```bash
# Via API (requires admin login)
curl -X POST http://localhost:5000/database/reset

# Or delete config.json and re-run setup wizard
```

---

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.