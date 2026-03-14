# AGENTS.md - Agent Coding Guidelines

This file provides guidance for AI agents working in this repository.

## Project Overview

A Flask web application for managing customers, products, and invoices with shopping cart functionality. Uses Flask-SQLAlchemy with PostgreSQL.

## Running the Application

### Installation
```bash
pip install -r requirements.txt
```

### Development Server
```bash
python app.py
```
Runs on http://localhost:5000 with debug mode enabled.

### Database
- PostgreSQL at localhost:5432
- Database name: `product`
- Credentials: `postgres` / `Zaq12wsX` (hardcoded, see app.py:9-10)
- Database tables are auto-created on startup

### Sample Data
- 3 customers (John Doe, Jane Smith, Bob Johnson)
- 5 products (ThinkPad, iPhone 14 Pro, iPad Air, Dell Monitor, Logitech Keyboard)
- Auto-loaded when database is empty

## Routes

| Endpoint | Description |
|----------|-------------|
| `/` | Dashboard with customer/product/invoice counts |
| `/customers` | View/add customers |
| `/products` | View/add/edit products |
| `/invoices` | Create invoices, view history |
| `/cart` | View/edit cart, checkout |
| `/cart/add/<id>` | Add product to cart |
| `/cart/remove/<id>` | Remove item from cart |
| `/cart/checkout` | Create invoice from cart |
| `/invoice/print/<id>` | Print specific invoice |

## Code Style Guidelines

### General Principles
- Keep functions small and focused (single responsibility)
- Use meaningful variable and function names
- Avoid code duplication; use helper functions
- Handle errors gracefully with appropriate flash messages

### Imports
- Standard library first, then third-party, then local
- Group by: os → flask → flask_sqlalchemy → other third-party → local models
- Example:
```python
import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from models import db, Customer, Product, Invoice, InvoiceItem
```

### Formatting
- Maximum line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Use blank lines to separate logical sections
- Put docstrings on complex functions

### Naming Conventions
- **Files**: lowercase with underscores (e.g., `app.py`, `models.py`)
- **Classes**: PascalCase (e.g., `Customer`, `InvoiceItem`)
- **Functions/variables**: snake_case (e.g., `get_cart()`, `cart_items`)
- **Constants**: UPPER_SNAKE_CASE
- **Database tables**: singular, lowercase (e.g., `customer`, `product`)

### SQLAlchemy Models
- Use `db.Model` as base class
- Define `__tablename__` explicitly (singular form)
- Use `db.Column` with explicit types
- Define foreign keys with `db.ForeignKey("table.column")`
- Use `db.relationship()` with `back_populates` for bidirectional relationships
- Add indexes for frequently queried columns using `__table_args__`

### Routes
- Use decorator `@app.route()` with explicit methods
- Validate form inputs before processing
- Use flash messages for user feedback (success/danger/warning)
- Always redirect after POST requests (post-redirect-get pattern)

### Error Handling
- Use `get_or_404()` for resource not found cases
- Validate stock availability before cart operations
- Check for empty cart before checkout
- Use try/except for database operations when needed

### Templates (Jinja2)
- Store in `templates/` directory
- Use Bootstrap 5 for responsive UI
- Use `url_for()` for all internal links
- Pass flash messages via `get_flashed_messages()` loop

### Currency
- All prices use LKR (Sri Lankan Rupee) format
- Display as integer or 2 decimal places

### Database Operations
- Use `db.session.add()` for new records
- Call `db.session.commit()` after modifications
- Use `db.session.flush()` to get auto-generated IDs
- Use `joinedload()` for eager loading relationships

### Cart Implementation
- Session-based cart using `session['cart']`
- Cart is list of dicts: `[{'product_id': int, 'quantity': int}]`
- Always validate stock before adding/updating cart items
- Clear cart after successful checkout

## Testing

No formal test framework is currently set up. To add tests:
```bash
pip install pytest pytest-flask
```

Run a single test:
```bash
pytest tests/test_file.py::test_function_name -v
```

Run all tests:
```bash
pytest
```

## Key Files

| File | Description |
|------|-------------|
| `app.py` | Flask application with all routes |
| `models.py` | SQLAlchemy ORM models |
| `forms.py` | WTForms (currently empty) |
| `templates/` | Jinja2 HTML templates |

## Configuration

- Secret key: `Zaq12wsX` (dev only)
- Database credentials can be overridden via environment variables:
  - `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`

## Security Notes

- Secret key is hardcoded for development only
- No authentication/authorization implemented
- Database credentials are in source code (not production-ready)
