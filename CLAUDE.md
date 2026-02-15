# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A simple Flask web application for managing customers, products, and invoices. Uses Flask-SQLAlchemy with PostgreSQL.

## Running the App

```bash
cd OneDrive/Documents/Product_App
pip install -r requirements.txt
python app.py
```

The app runs on http://localhost:5000 with debug mode enabled.

## Database

- PostgreSQL at localhost:5432
- Database name: `product`
- Tables are auto-created on startup via `db.create_all()`

## Architecture

- **app.py** - Main Flask application with all routes (home, customers, products, invoices)
- **models.py** - SQLAlchemy models: Customer, Product, Invoice with relationships
- **templates/** - Jinja2 HTML templates (base.html, customers.html, products.html, invoices.html)
- **forms.py** - Currently unused (WTForms dependencies installed but not used)

## Key Patterns

- Routes render templates and pass query results: `Customer.query.all()`
- Form submissions use `request.form` directly (no WTForms validation currently)
- Relationships: Customer ← Invoice → Product (one-to-many)

## Known Issues

- Typo in field names: `phone_numbet` (should be `phone_number`)
- Empty forms.py - no form validation implemented
- Database credentials are hardcoded in app.py config
