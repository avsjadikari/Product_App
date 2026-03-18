"""
RESTful API endpoints for the POS application.
Provides JSON endpoints for mobile apps and external integrations.
"""
from flask import Blueprint, jsonify, request, current_app
from flask_sqlalchemy import SQLAlchemy
from models import db, Product, Customer, Invoice, InvoiceItem, StockMovement
from functools import wraps
import logging

api = Blueprint('api', __name__, url_prefix='/api/v1')
api_logger = logging.getLogger(__name__)


def api_login_required(f):
    """API authentication decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def log_api_request(endpoint: str):
    """Log API requests for monitoring."""
    username = session.get('username', 'Anonymous') if 'user_id' in session else 'Unauthenticated'
    ip_address = request.remote_addr
    api_logger.info(f"API: {username} | {request.method} {endpoint} | IP: {ip_address}")


# ============ API HEALTH CHECK ============

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    log_api_request('/health')
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 503


# ============ PRODUCTS API ============

@api.route('/products', methods=['GET'])
def get_products():
    """Get all active products."""
    log_api_request('/products')
    search = request.args.get('search', '')
    product_type = request.args.get('type', '')
    low_stock = request.args.get('low_stock', '').lower() == 'true'
    
    query = Product.query.filter_by(is_active=True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.product_name.ilike(search_term),
                Product.product_model.ilike(search_term),
                Product.product_type.ilike(search_term)
            )
        )
    
    if product_type:
        query = query.filter_by(product_type=product_type)
    
    if low_stock:
        query = query.filter(Product.product_quantity <= Product.low_stock_threshold)
    
    products = query.order_by(Product.product_name).all()
    
    return jsonify({
        'products': [{
            'id': p.product_id,
            'name': p.product_name,
            'type': p.product_type,
            'model': p.product_model,
            'color': p.product_color,
            'price': float(p.product_price),
            'quantity': p.product_quantity,
            'low_stock_threshold': p.low_stock_threshold,
            'is_low_stock': p.is_low_stock
        } for p in products],
        'count': len(products)
    })


@api.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID."""
    log_api_request(f'/products/{product_id}')
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'id': product.product_id,
        'name': product.product_name,
        'type': product.product_type,
        'model': product.product_model,
        'color': product.product_color,
        'price': float(product.product_price),
        'quantity': product.product_quantity,
        'low_stock_threshold': product.low_stock_threshold,
        'is_low_stock': product.is_low_stock,
        'created_at': product.created_at.isoformat() if product.created_at else None
    })


# ============ CUSTOMERS API ============

@api.route('/customers', methods=['GET'])
def get_customers():
    """Get all active customers."""
    log_api_request('/customers')
    search = request.args.get('search', '')
    
    query = Customer.query.filter_by(is_active=True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Customer.first_name.ilike(search_term),
                Customer.last_name.ilike(search_term),
                Customer.phone_number.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        )
    
    customers = query.order_by(Customer.first_name, Customer.last_name).all()
    
    return jsonify({
        'customers': [{
            'id': c.customer_id,
            'name': c.full_name,
            'phone': c.phone_number,
            'email': c.email,
            'address': c.customer_address
        } for c in customers],
        'count': len(customers)
    })


@api.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get a single customer by ID."""
    log_api_request(f'/customers/{customer_id}')
    customer = Customer.query.get_or_404(customer_id)
    
    return jsonify({
        'id': customer.customer_id,
        'name': customer.full_name,
        'first_name': customer.first_name,
        'last_name': customer.last_name,
        'phone': customer.phone_number,
        'email': customer.email,
        'address': customer.customer_address,
        'created_at': customer.created_at.isoformat() if customer.created_at else None
    })


# ============ INVOICES API ============

@api.route('/invoices', methods=['GET'])
def get_invoices():
    """Get invoices with optional filters."""
    log_api_request('/invoices')
    status = request.args.get('status', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    query = Invoice.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'invoices': [{
            'id': inv.invoice_id,
            'number': inv.invoice_number,
            'customer': inv.customer.full_name if inv.customer else 'Unknown',
            'status': inv.status,
            'total': float(inv.total),
            'subtotal': float(inv.subtotal),
            'tax_amount': float(inv.tax_amount),
            'discount_amount': float(inv.discount_amount),
            'created_at': inv.created_at.isoformat() if inv.created_at else None
        } for inv in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@api.route('/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    """Get a single invoice with items."""
    log_api_request(f'/invoices/{invoice_id}')
    invoice = Invoice.query.get_or_404(invoice_id)
    
    return jsonify({
        'id': invoice.invoice_id,
        'number': invoice.invoice_number,
        'customer': invoice.customer.full_name if invoice.customer else 'Unknown',
        'customer_id': invoice.customer_details,
        'status': invoice.status,
        'subtotal': float(invoice.subtotal),
        'tax_rate': float(invoice.tax_rate),
        'tax_amount': float(invoice.tax_amount),
        'discount_amount': float(invoice.discount_amount),
        'total': float(invoice.total),
        'payment_method': invoice.payment_method,
        'payment_date': invoice.payment_date.isoformat() if invoice.payment_date else None,
        'notes': invoice.notes,
        'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
        'items': [{
            'id': item.item_id,
            'product_name': item.product.product_name if item.product else 'Unknown',
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),
            'discount_amount': float(item.discount_amount),
            'total': float(item.total)
        } for item in invoice.items]
    })


# ============ STOCK API ============

@api.route('/stock', methods=['GET'])
def get_stock():
    """Get stock levels for all products."""
    log_api_request('/stock')
    
    products = Product.query.filter_by(is_active=True).order_by(
        Product.product_quantity.asc()
    ).all()
    
    low_stock = [p for p in products if p.is_low_stock]
    out_of_stock = [p for p in products if p.product_quantity == 0]
    
    return jsonify({
        'products': [{
            'id': p.product_id,
            'name': p.product_name,
            'quantity': p.product_quantity,
            'threshold': p.low_stock_threshold,
            'is_low_stock': p.is_low_stock
        } for p in products],
        'low_stock_count': len(low_stock),
        'out_of_stock_count': len(out_of_stock),
        'total_products': len(products)
    })


@api.route('/stock/movements', methods=['GET'])
def get_stock_movements():
    """Get stock movement history."""
    log_api_request('/stock/movements')
    
    product_id = request.args.get('product_id')
    movement_type = request.args.get('type')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    query = StockMovement.query
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    if movement_type:
        query = query.filter_by(movement_type=movement_type)
    
    pagination = query.order_by(
        StockMovement.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'movements': [{
            'id': m.movement_id,
            'product_name': m.product.product_name if m.product else 'Unknown',
            'type': m.movement_type,
            'quantity': m.quantity,
            'reference_type': m.reference_type,
            'reference_id': m.reference_id,
            'notes': m.notes,
            'created_at': m.created_at.isoformat() if m.created_at else None
        } for m in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


# ============ DASHBOARD API ============

@api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard statistics."""
    log_api_request('/dashboard')
    
    total_customers = Customer.query.filter_by(is_active=True).count()
    total_products = Product.query.filter_by(is_active=True).count()
    total_invoices = Invoice.query.count()
    pending_invoices = Invoice.query.filter_by(status='pending').count()
    paid_invoices = Invoice.query.filter_by(status='paid').count()
    total_revenue = db.session.query(db.func.sum(Invoice.total)).filter(
        Invoice.status == 'paid'
    ).scalar() or 0
    
    low_stock_products = Product.query.filter(
        Product.product_quantity <= Product.low_stock_threshold,
        Product.is_active == True
    ).count()
    
    return jsonify({
        'stats': {
            'customers': total_customers,
            'products': total_products,
            'invoices': total_invoices,
            'pending_invoices': pending_invoices,
            'paid_invoices': paid_invoices,
            'total_revenue': float(total_revenue),
            'low_stock_alerts': low_stock_products
        }
    })


# ============ API DOCUMENTATION ============

@api.route('/docs', methods=['GET'])
def api_docs():
    """Return API documentation."""
    return jsonify({
        'title': 'POS Application API',
        'version': '1.0.0',
        'endpoints': {
            'health': 'GET /api/v1/health - Health check',
            'products': 'GET /api/v1/products - List products (supports ?search=, ?type=, ?low_stock=)',
            'product_detail': 'GET /api/v1/products/<id> - Get product details',
            'customers': 'GET /api/v1/customers - List customers (supports ?search=)',
            'customer_detail': 'GET /api/v1/customers/<id> - Get customer details',
            'invoices': 'GET /api/v1/invoices - List invoices (supports ?status=, ?page=)',
            'invoice_detail': 'GET /api/v1/invoices/<id> - Get invoice with items',
            'stock': 'GET /api/v1/stock - Get stock levels',
            'stock_movements': 'GET /api/v1/stock/movements - Get movement history',
            'dashboard': 'GET /api/v1/dashboard - Get dashboard stats'
        }
    })