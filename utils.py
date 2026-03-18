"""
Utility functions for the POS application.
Includes data export (CSV), formatting, and search helpers.
"""
import csv
import io
from datetime import datetime
from flask import Response, request
from sqlalchemy import or_
from models import Product, Customer, Invoice, InvoiceItem


# ============ CSV EXPORT FUNCTIONS ============

def export_products_csv(products):
    """Export products to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        'ID', 'Type', 'Name', 'Model', 'Color', 
        'Price', 'Quantity', 'Low Stock Threshold', 'Is Low Stock'
    ])
    
    # Data rows
    for p in products:
        writer.writerow([
            p.product_id,
            p.product_type,
            p.product_name,
            p.product_model,
            p.product_color,
            f"{p.product_price:.2f}",
            p.product_quantity,
            p.low_stock_threshold,
            'Yes' if p.is_low_stock else 'No'
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=products_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


def export_customers_csv(customers):
    """Export customers to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'First Name', 'Last Name', 'Phone', 'Email', 'Address'])
    
    for c in customers:
        writer.writerow([
            c.customer_id,
            c.first_name,
            c.last_name,
            c.phone_number,
            c.email or '',
            c.customer_address
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=customers_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


def export_invoices_csv(invoices):
    """Export invoices to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Invoice #', 'Customer', 'Status', 'Subtotal', 
        'Tax', 'Discount', 'Total', 'Created Date', 'Payment Method'
    ])
    
    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.customer.full_name if inv.customer else 'Unknown',
            inv.status,
            f"{inv.subtotal:.2f}",
            f"{inv.tax_amount:.2f}",
            f"{inv.discount_amount:.2f}",
            f"{inv.total:.2f}",
            inv.created_at.strftime('%Y-%m-%d %H:%M') if inv.created_at else '',
            inv.payment_method or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=invoices_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


def export_sales_report_csv(invoices, total_sales, total_tax, total_discount):
    """Export sales report to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Report header
    writer.writerow(['Sales Report'])
    writer.writerow(['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Summary
    writer.writerow(['Summary'])
    writer.writerow(['Total Sales', f"{total_sales:.2f}"])
    writer.writerow(['Total Tax', f"{total_tax:.2f}"])
    writer.writerow(['Total Discount', f"{total_discount:.2f}"])
    writer.writerow(['Net Total', f"{total_sales - total_tax - total_discount:.2f}"])
    writer.writerow([])
    
    # Header
    writer.writerow([
        'Invoice #', 'Customer', 'Date', 'Status', 
        'Subtotal', 'Tax', 'Discount', 'Total'
    ])
    
    # Detail rows
    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.customer.full_name if inv.customer else 'Unknown',
            inv.created_at.strftime('%Y-%m-%d') if inv.created_at else '',
            inv.status,
            f"{inv.subtotal:.2f}",
            f"{inv.tax_amount:.2f}",
            f"{inv.discount_amount:.2f}",
            f"{inv.total:.2f}"
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=sales_report_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


# ============ PAGINATION HELPER ============

class PaginationHelper:
    """Helper class for pagination calculations."""
    
    def __init__(self, page, per_page, total):
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page
    
    @property
    def has_prev(self):
        return self.page > 1
    
    @property
    def has_next(self):
        return self.page < self.pages
    
    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_num(self):
        return self.page + 1 if self.has_next else None
    
    def get_page_range(self, show_pages=5):
        """Get a range of page numbers to display."""
        start = max(1, self.page - show_pages // 2)
        end = min(self.pages, start + show_pages - 1)
        start = max(1, end - show_pages + 1)
        return range(start, end + 1)


# ============ SEARCH HELPER ============

def search_products(search_term, base_query=None):
    """Search products by name, model, or type."""
    if base_query is None:
        base_query = Product.query.filter_by(is_active=True)
    
    if not search_term:
        return base_query
    
    term = f"%{search_term}%"
    return base_query.filter(
        or_(
            Product.product_name.ilike(term),
            Product.product_model.ilike(term),
            Product.product_type.ilike(term),
            Product.product_color.ilike(term)
        )
    )


def search_customers(search_term, base_query=None):
    """Search customers by name, phone, or email."""
    if base_query is None:
        base_query = Customer.query.filter_by(is_active=True)
    
    if not search_term:
        return base_query
    
    term = f"%{search_term}%"
    return base_query.filter(
        or_(
            Customer.first_name.ilike(term),
            Customer.last_name.ilike(term),
            Customer.phone_number.ilike(term),
            Customer.email.ilike(term)
        )
    )


def search_invoices(search_term, base_query=None):
    """Search invoices by invoice number or customer name."""
    if base_query is None:
        base_query = Invoice.query
    
    if not search_term:
        return base_query
    
    term = f"%{search_term}%"
    return base_query.join(Customer).filter(
        or_(
            Invoice.invoice_number.ilike(term),
            Customer.first_name.ilike(term),
            Customer.last_name.ilike(term)
        )
    )


# ============ FORMATTING HELPER ============

def format_currency(amount):
    """Format amount as LKR currency."""
    return f"Rs. {amount:,.2f}"


def format_date(date_obj, format='%Y-%m-%d'):
    """Format date object to string."""
    if not date_obj:
        return ''
    return date_obj.strftime(format)


# ============ VALIDATION HELPER ============

def validate_positive_integer(value, field_name='value'):
    """Validate that a value is a positive integer."""
    try:
        int_val = int(value)
        if int_val < 0:
            raise ValueError(f"{field_name} must be positive")
        return int_val
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}")


def validate_positive_float(value, field_name='value'):
    """Validate that a value is a positive number."""
    try:
        float_val = float(value)
        if float_val < 0:
            raise ValueError(f"{field_name} must be positive")
        return float_val
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}")