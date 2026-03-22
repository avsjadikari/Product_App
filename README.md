Project Overview

A Flask-based Point of Sale (POS) application for managing customers, products, invoices, and inventory. Features include shopping cart, invoice generation, stock tracking, and sales reporting.
Running the Application

pip install -r requirements.txt
python app.py

The app runs on http://localhost:5000 with debug mode enabled. Database tables are auto-created on startup.
Architecture
Tech Stack

    Framework: Flask with Flask-SQLAlchemy
    Database: PostgreSQL (localhost:5432, database: product)
    ORM: SQLAlchemy with explicit relationships and indexes
    Frontend: Jinja2 templates with Bootstrap 5

File Structure

app.py          # Main Flask application with all routes
models.py       # SQLAlchemy ORM models (User, Customer, Product, Invoice, InvoiceItem, StockMovement)
forms.py        # WTForms (currently unused)
templates/      # Jinja2 HTML templates

Database Models
Model 	Purpose
User 	Authentication with roles (admin/user), password hashing
Customer 	Customer records with name, phone, address
Product 	Inventory items with type, name, model, color, price, quantity
Invoice 	Sales transactions linked to customers
InvoiceItem 	Line items within invoices
StockMovement 	Audit trail for inventory changes (sales, adjustments, returns)
Key Patterns

Authentication: Session-based with @login_required and @admin_required decorators. Passwords hashed with werkzeug.

Cart: Session-based (session['cart'] as list of {'product_id': int, 'quantity': int}). Validates stock before operations.

Stock Management: Automatic deduction on invoice checkout, returns stock on invoice cancellation/deletion. All movements tracked via StockMovement model.

Invoice Workflow: Draft → Pending → Paid (or Cancelled). Only draft/pending invoices can be edited.
Common Tasks

Add a new route: Add @app.route() decorator in app.py with appropriate auth decorator.

Add a model field: Add to model class in models.py, then run db.drop_all() and db.create_all() (or use migrations).

Add a template: Create HTML in templates/ using Bootstrap 5 classes, extend base.html.
Configuration

Environment variables (with defaults):

    SECRET_KEY: Flask session secret
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME: PostgreSQL connection

Default credentials: postgres / Zaq12wsX (for localhost)
Security Note

The app has hardcoded credentials and secret key for development only. Before production deployment, move all secrets to environment variables and use strong credentials.
