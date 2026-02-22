# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask web application for managing customers, products, and invoices with shopping cart functionality. Uses Flask-SQLAlchemy with PostgreSQL.

## Running the App

```bash
cd OneDrive/Documents/Product_App
pip install -r requirements.txt
python app.py
```

The app runs on http://localhost:5000 with debug mode enabled. Database tables are auto-created on startup.

## Database

- PostgreSQL at localhost:5432
- Database name: `product`
- Credentials hardcoded in app.py config

## Architecture

- **app.py** - Flask application with routes for home, customers, products, cart, invoices
- **models.py** - SQLAlchemy models: Customer, Product, Invoice, InvoiceItem
- **templates/** - Jinja2 HTML templates with Bootstrap 5 mobile-responsive UI

## Database Schema

- **Customer** - customer_id, first_name, last_name, phone_number, customer_address
- **Product** - product_id, product_type, product_name, product_model, product_color, product_price, product_quantity
- **Invoice** - invoice_id, customer_details (FK), created_at
- **InvoiceItem** - item_id, invoice_id (FK), product_details (FK), quantity, unit_price

One Invoice can have multiple InvoiceItems (cart checkout creates single invoice with multiple items).

## Key Features

- **Shopping Cart** - Session-based cart supporting multiple products with different quantities
- **Stock Management** - Quantity deducted from product stock on invoice creation
- **Invoice Printing** - Each invoice can be printed with full details
- **Sample Data** - Auto-loaded on first run (3 customers, 5 products)

## Routes

- `/` - Dashboard with counts
- `/customers` - Add/view customers
- `/products` - Add/edit/view products
- `/invoices` - Create invoice (add to cart), view history
- `/cart` - View/edit cart, checkout
- `/invoice/print/<id>` - Print specific invoice

## Currency

All prices use LKR (Sri Lankan Rupee) format throughout the app.
