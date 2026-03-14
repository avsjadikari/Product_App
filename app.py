import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from models import db, User, Customer, Product, Invoice, InvoiceItem, StockMovement

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Zaq12wsX')
db_user = os.environ.get('DB_USER', 'postgres')
db_pass = os.environ.get('DB_PASSWORD', 'Zaq12wsX')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', '5432')
db_name = os.environ.get('DB_NAME', 'product')
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEFAULT_TAX_RATE'] = 0

db.init_app(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())


with app.app_context():
    try:
        db.drop_all()
    except:
        pass
    db.create_all()

    if User.query.count() == 0:
        admin = User(username='admin', role='admin', force_password_change=True)
        admin.set_password('admin123')
        db.session.add(admin)

        user = User(username='user', role='user')
        user.set_password('user123')
        db.session.add(user)

        db.session.commit()

    if Customer.query.count() == 0:
        customers = [
            Customer(first_name="John", last_name="Doe", phone_number="1234567890", customer_address="123 Main St", email="john@example.com"),
            Customer(first_name="Jane", last_name="Smith", phone_number="9876543210", customer_address="456 Oak Ave", email="jane@example.com"),
            Customer(first_name="Bob", last_name="Johnson", phone_number="5551234567", customer_address="789 Pine Rd", email="bob@example.com"),
        ]
        for c in customers:
            db.session.add(c)

        products = [
            Product(product_type="Laptop", product_name="ThinkPad", product_model="T490", product_color="Black", product_price=999.99, product_quantity=10, low_stock_threshold=5),
            Product(product_type="Phone", product_name="iPhone", product_model="14 Pro", product_color="Silver", product_price=1099.99, product_quantity=15, low_stock_threshold=5),
            Product(product_type="Tablet", product_name="iPad", product_model="Air", product_color="Gold", product_price=599.99, product_quantity=8, low_stock_threshold=5),
            Product(product_type="Monitor", product_name="Dell UltraSharp", product_model="U2720Q", product_color="Black", product_price=449.99, product_quantity=5, low_stock_threshold=3),
            Product(product_type="Keyboard", product_name="Logitech MX", product_model="Master 3", product_color="Grey", product_price=99.99, product_quantity=20, low_stock_threshold=5),
        ]
        for p in products:
            db.session.add(p)

        db.session.commit()


def get_cart():
    return session.get('cart', [])


def save_cart(cart):
    session['cart'] = cart


def record_stock_movement(product_id, movement_type, quantity, reference_type=None, reference_id=None, notes=None, created_by=None):
    movement = StockMovement(
        product_id=product_id,
        movement_type=movement_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        created_by=created_by
    )
    db.session.add(movement)
    return movement


def update_stock(product_id, quantity_change, movement_type, reference_type=None, reference_id=None, notes=None):
    product = Product.query.get_or_404(product_id)
    new_quantity = product.product_quantity + quantity_change
    
    if new_quantity < 0:
        return False, f"Insufficient stock for {product.product_name}. Available: {product.product_quantity}"
    
    product.product_quantity = new_quantity
    record_stock_movement(
        product_id=product_id,
        movement_type=movement_type,
        quantity=abs(quantity_change),
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes
    )
    return True, "Stock updated successfully"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['role'] = user.role
            
            if user.force_password_change:
                flash("You must change your password before continuing.", "warning")
                return redirect(url_for('change_password'))
            
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "danger")
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    
    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('change_password'))
        
        if len(new_password) < 4:
            flash("Password must be at least 4 characters.", "danger")
            return redirect(url_for('change_password'))
        
        user.set_password(new_password)
        user.force_password_change = False
        db.session.commit()
        flash("Password changed successfully!", "success")
        return redirect(url_for('home'))
    
    return render_template("change_password.html", user=user)


@app.route("/")
@login_required
def home():
    stats = {
        'customers': Customer.query.filter_by(is_active=True).count(),
        'products': Product.query.filter_by(is_active=True).count(),
        'invoices': Invoice.query.count(),
        'pending_invoices': Invoice.query.filter_by(status='pending').count(),
        'paid_invoices': Invoice.query.filter_by(status='paid').count(),
    }
    low_stock_products = Product.query.filter(
        Product.product_quantity <= Product.low_stock_threshold,
        Product.is_active == True
    ).all()
    recent_invoices = Invoice.query.options(
        joinedload(Invoice.customer)
    ).order_by(Invoice.created_at.desc()).limit(5).all()
    
    total_revenue = db.session.query(db.func.sum(Invoice.total)).filter(Invoice.status == 'paid').scalar() or 0
    
    return render_template("home.html", stats=stats, low_stock_products=low_stock_products, 
                          recent_invoices=recent_invoices, total_revenue=total_revenue)


@app.route("/users")
@admin_required
def users():
    return render_template("users.html", users=User.query.all())


@app.route("/users/add", methods=["POST"])
@admin_required
def add_user():
    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]
    
    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "danger")
        return redirect(url_for('users'))
    
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f"User {username} created successfully!", "success")
    return redirect(url_for('users'))


@app.route("/users/delete/<int:id>")
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.user_id == session.get('user_id'):
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for('users'))
    username = user.username
    user.is_active = False
    db.session.commit()
    flash(f"User {username} deleted successfully!", "success")
    return redirect(url_for('users'))


@app.route("/database/reset", methods=["POST"])
@admin_required
def reset_database():
    try:
        db.drop_all()
        db.create_all()

        admin = User(username='admin', role='admin', force_password_change=True)
        admin.set_password('admin123')
        db.session.add(admin)

        user = User(username='user', role='user')
        user.set_password('user123')
        db.session.add(user)

        customers = [
            Customer(first_name="John", last_name="Doe", phone_number="1234567890", customer_address="123 Main St", email="john@example.com"),
            Customer(first_name="Jane", last_name="Smith", phone_number="9876543210", customer_address="456 Oak Ave", email="jane@example.com"),
            Customer(first_name="Bob", last_name="Johnson", phone_number="5551234567", customer_address="789 Pine Rd", email="bob@example.com"),
        ]
        for c in customers:
            db.session.add(c)

        products = [
            Product(product_type="Laptop", product_name="ThinkPad", product_model="T490", product_color="Black", product_price=999.99, product_quantity=10, low_stock_threshold=5),
            Product(product_type="Phone", product_name="iPhone", product_model="14 Pro", product_color="Silver", product_price=1099.99, product_quantity=15, low_stock_threshold=5),
            Product(product_type="Tablet", product_name="iPad", product_model="Air", product_color="Gold", product_price=599.99, product_quantity=8, low_stock_threshold=5),
            Product(product_type="Monitor", product_name="Dell UltraSharp", product_model="U2720Q", product_color="Black", product_price=449.99, product_quantity=5, low_stock_threshold=3),
            Product(product_type="Keyboard", product_name="Logitech MX", product_model="Master 3", product_color="Grey", product_price=99.99, product_quantity=20, low_stock_threshold=5),
        ]
        for p in products:
            db.session.add(p)

        db.session.commit()
        session.clear()
        flash("Database reset successfully! Please login with default credentials and change your password.", "success")
    except Exception as e:
        flash(f"Error resetting database: {str(e)}", "danger")
    
    return redirect(url_for('login'))


@app.route("/customers")
@login_required
def customers():
    return render_template("customers.html", customers=Customer.query.filter_by(is_active=True).all())


@app.route("/customers/add", methods=["POST"])
@login_required
def add_customer():
    db.session.add(Customer(
        first_name=request.form["first_name"],
        last_name=request.form["last_name"],
        phone_number=request.form["phone_number"],
        customer_address=request.form["customer_address"],
        email=request.form.get("email", "")
    ))
    db.session.commit()
    flash("Customer added successfully!", "success")
    return redirect(url_for("customers"))


@app.route("/customers/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == "POST":
        customer.first_name = request.form["first_name"]
        customer.last_name = request.form["last_name"]
        customer.phone_number = request.form["phone_number"]
        customer.customer_address = request.form["customer_address"]
        customer.email = request.form.get("email", "")
        db.session.commit()
        flash("Customer updated successfully!", "success")
        return redirect(url_for("customers"))
    return render_template("edit_customer.html", customer=customer)


@app.route("/customers/delete/<int:id>")
@admin_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    customer.is_active = False
    db.session.commit()
    flash("Customer deleted successfully!", "success")
    return redirect(url_for("customers"))


@app.route("/products")
@login_required
def products():
    return render_template("products.html", products=Product.query.filter_by(is_active=True).all())


@app.route("/products/add", methods=["POST"])
@login_required
def add_product():
    db.session.add(Product(
        product_type=request.form["product_type"],
        product_name=request.form["product_name"],
        product_model=request.form["product_model"],
        product_color=request.form["product_color"],
        product_price=float(request.form["product_price"]),
        product_quantity=int(request.form["product_quantity"]),
        low_stock_threshold=int(request.form.get("low_stock_threshold", 5))
    ))
    db.session.commit()
    flash("Product added successfully!", "success")
    return redirect(url_for("products"))


@app.route("/products/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        old_quantity = product.product_quantity
        product.product_type = request.form["product_type"]
        product.product_name = request.form["product_name"]
        product.product_model = request.form["product_model"]
        product.product_color = request.form["product_color"]
        product.product_price = float(request.form["product_price"])
        product.low_stock_threshold = int(request.form.get("low_stock_threshold", 5))
        
        new_quantity = int(request.form["product_quantity"])
        if new_quantity != old_quantity:
            quantity_diff = new_quantity - old_quantity
            if quantity_diff > 0:
                record_stock_movement(product.product_id, 'adjustment_in', quantity_diff, notes="Product edit adjustment")
            else:
                record_stock_movement(product.product_id, 'adjustment_out', abs(quantity_diff), notes="Product edit adjustment")
            product.product_quantity = new_quantity
        
        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for("products"))
    return render_template("edit_product.html", product=product)


@app.route("/products/delete/<int:id>")
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    product.is_active = False
    db.session.commit()
    flash("Product deleted successfully!", "success")
    return redirect(url_for("products"))


@app.route("/stock")
@login_required
def stock_management():
    products = Product.query.filter_by(is_active=True).order_by(Product.product_quantity.asc()).all()
    movements = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(50).all()
    return render_template("stock.html", products=products, movements=movements)


@app.route("/stock/adjust", methods=["POST"])
@login_required
def stock_adjust():
    product_id = int(request.form["product_id"])
    adjustment = int(request.form["quantity"])
    notes = request.form.get("notes", "")
    
    success, message = update_stock(
        product_id=product_id,
        quantity_change=adjustment,
        movement_type='adjustment_in' if adjustment > 0 else 'adjustment_out',
        reference_type='manual',
        notes=notes
    )
    
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    
    return redirect(url_for("stock_management"))


@app.route("/cart")
@login_required
def cart():
    cart_items = get_cart()
    cart_products = []
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            cart_products.append({
                'product': product,
                'quantity': item['quantity']
            })
    return render_template("cart.html", cart_products=cart_products, customers=Customer.query.filter_by(is_active=True).all())


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def cart_add(product_id):
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get_or_404(product_id)
    cart = get_cart()

    for item in cart:
        if item['product_id'] == product_id:
            total = item['quantity'] + quantity
            if total > product.product_quantity:
                flash(f"Insufficient stock! Available: {product.product_quantity}", "danger")
            else:
                item['quantity'] = total
                save_cart(cart)
                flash(f"Updated {product.product_name} quantity in cart", "success")
            return redirect(url_for("cart"))

    if quantity > product.product_quantity:
        flash(f"Insufficient stock! Available: {product.product_quantity}", "danger")
        return redirect(url_for("invoices"))

    cart.append({'product_id': product_id, 'quantity': quantity})
    save_cart(cart)
    flash(f"Added {product.product_name} to cart", "success")
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:product_id>")
@login_required
def cart_remove(product_id):
    cart = get_cart()
    cart = [item for item in cart if item['product_id'] != product_id]
    save_cart(cart)
    flash("Item removed from cart", "success")
    return redirect(url_for("cart"))


@app.route("/cart/update/<int:product_id>", methods=["POST"])
@login_required
def cart_update(product_id):
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get_or_404(product_id)
    cart = get_cart()
    for item in cart:
        if item['product_id'] == product_id:
            if quantity > product.product_quantity + item['quantity']:
                flash(f"Insufficient stock! Available: {product.product_quantity + item['quantity']}", "danger")
            else:
                item['quantity'] = quantity
                save_cart(cart)
                flash(f"Updated {product.product_name} quantity", "success")
            break
    return redirect(url_for("cart"))


@app.route("/cart/clear")
@login_required
def cart_clear():
    save_cart([])
    flash("Cart cleared", "success")
    return redirect(url_for("cart"))


@app.route("/cart/checkout", methods=["POST"])
@login_required
def cart_checkout():
    customer_id = int(request.form["customer_id"])
    tax_rate = float(request.form.get("tax_rate", 0))
    discount_amount = float(request.form.get("discount_amount", 0))
    cart = get_cart()

    if not cart:
        flash("Cart is empty", "warning")
        return redirect(url_for("invoices"))

    for item in cart:
        product = Product.query.get(item['product_id'])
        if not product or product.product_quantity < item['quantity']:
            flash(f"Insufficient stock for {product.product_name if product else 'product'}", "danger")
            return redirect(url_for("cart"))

    invoice = Invoice(
        customer_details=customer_id,
        invoice_number=Invoice.generate_invoice_number(),
        status='pending',
        tax_rate=tax_rate,
        discount_amount=discount_amount
    )
    db.session.add(invoice)
    db.session.flush()

    for item in cart:
        product = Product.query.get(item['product_id'])
        invoice_item = InvoiceItem(
            invoice_id=invoice.invoice_id,
            product_details=item['product_id'],
            quantity=item['quantity'],
            unit_price=product.product_price
        )
        invoice_item.calculate_total()
        db.session.add(invoice_item)
        
        product.product_quantity -= item['quantity']
        record_stock_movement(
            product_id=item['product_id'],
            movement_type='sale',
            quantity=item['quantity'],
            reference_type='invoice',
            reference_id=invoice.invoice_id
        )

    invoice.calculate_totals()
    db.session.commit()
    save_cart([])
    flash(f"Invoice {invoice.invoice_number} created successfully!", "success")
    return redirect(url_for("invoice_print", invoice_id=invoice.invoice_id))


@app.route("/invoices")
@login_required
def invoices():
    status_filter = request.args.get("status", "all")
    query = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product)
    )
    
    if status_filter != "all":
        query = query.filter(Invoice.status == status_filter)
    
    invoices_list = query.order_by(Invoice.created_at.desc()).all()
    available_products = Product.query.filter(Product.product_quantity > 0, Product.is_active == True).all()
    
    return render_template("invoices.html", 
                          invoices=invoices_list, 
                          customers=Customer.query.filter_by(is_active=True).all(), 
                          products=available_products, 
                          cart_count=len(get_cart()),
                          current_status=status_filter)


@app.route("/invoices/create", methods=["POST"])
@login_required
def create_invoice():
    customer_id = int(request.form["customer_id"])
    invoice = Invoice(
        customer_details=customer_id,
        invoice_number=Invoice.generate_invoice_number(),
        status='draft'
    )
    db.session.add(invoice)
    db.session.flush()
    return redirect(url_for("edit_invoice", invoice_id=invoice.invoice_id))


@app.route("/invoices/edit/<int:invoice_id>", methods=["GET", "POST"])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product)
    ).get_or_404(invoice_id)
    
    if not invoice.can_edit:
        flash("Cannot edit a paid or cancelled invoice", "danger")
        return redirect(url_for("invoices"))
    
    if request.method == "POST":
        invoice.tax_rate = float(request.form.get("tax_rate", 0))
        invoice.discount_amount = float(request.form.get("discount_amount", 0))
        invoice.notes = request.form.get("notes", "")
        invoice.calculate_totals()
        db.session.commit()
        flash("Invoice updated!", "success")
        return redirect(url_for("edit_invoice", invoice_id=invoice_id))
    
    available_products = Product.query.filter(Product.product_quantity > 0, Product.is_active == True).all()
    return render_template("edit_invoice.html", invoice=invoice, products=available_products)


@app.route("/invoices/add-item/<int:invoice_id>", methods=["POST"])
@login_required
def add_invoice_item(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if not invoice.can_edit:
        flash("Cannot modify a paid or cancelled invoice", "danger")
        return redirect(url_for("invoices"))
    
    product_id = int(request.form["product_id"])
    quantity = int(request.form["quantity"])
    product = Product.query.get_or_404(product_id)
    
    existing_item = InvoiceItem.query.filter_by(invoice_id=invoice_id, product_details=product_id).first()
    if existing_item:
        new_qty = existing_item.quantity + quantity
        if new_qty > product.product_quantity + existing_item.quantity:
            flash(f"Insufficient stock! Available: {product.product_quantity + existing_item.quantity}", "danger")
        else:
            existing_item.quantity = new_qty
            existing_item.calculate_total()
            product.product_quantity -= quantity
            record_stock_movement(product_id, 'sale', quantity, 'invoice', invoice_id)
            invoice.calculate_totals()
            db.session.commit()
            flash("Item quantity updated!", "success")
    else:
        if quantity > product.product_quantity:
            flash(f"Insufficient stock! Available: {product.product_quantity}", "danger")
        else:
            item = InvoiceItem(
                invoice_id=invoice_id,
                product_details=product_id,
                quantity=quantity,
                unit_price=product.product_price
            )
            item.calculate_total()
            db.session.add(item)
            product.product_quantity -= quantity
            record_stock_movement(product_id, 'sale', quantity, 'invoice', invoice_id)
            invoice.calculate_totals()
            db.session.commit()
            flash("Item added to invoice!", "success")
    
    return redirect(url_for("edit_invoice", invoice_id=invoice_id))


@app.route("/invoices/remove-item/<int:item_id>")
@login_required
def remove_invoice_item(item_id):
    item = InvoiceItem.query.get_or_404(item_id)
    invoice = Invoice.query.get(item.invoice_id)
    
    if not invoice.can_edit:
        flash("Cannot modify a paid or cancelled invoice", "danger")
        return redirect(url_for("invoices"))
    
    product = Product.query.get(item.product_details)
    product.product_quantity += item.quantity
    record_stock_movement(item.product_details, 'return', item.quantity, 'invoice', invoice.invoice_id, notes="Item removed from invoice")
    
    invoice_id = item.invoice_id
    db.session.delete(item)
    invoice.calculate_totals()
    db.session.commit()
    flash("Item removed from invoice!", "success")
    return redirect(url_for("edit_invoice", invoice_id=invoice_id))


@app.route("/invoices/update-status/<int:invoice_id>", methods=["POST"])
@login_required
def update_invoice_status(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    new_status = request.form["status"]
    
    if new_status == "paid":
        invoice.status = "paid"
        invoice.payment_method = request.form.get("payment_method", "")
        invoice.payment_reference = request.form.get("payment_reference", "")
        invoice.payment_date = datetime.now()
        flash(f"Invoice {invoice.invoice_number} marked as paid!", "success")
    elif new_status == "cancelled":
        if invoice.can_cancel:
            for item in invoice.items:
                product = Product.query.get(item.product_details)
                product.product_quantity += item.quantity
                record_stock_movement(item.product_details, 'return', item.quantity, 'invoice', invoice_id, notes="Invoice cancelled")
            invoice.status = "cancelled"
            flash(f"Invoice {invoice.invoice_number} cancelled and stock returned!", "success")
        else:
            flash("Cannot cancel this invoice", "danger")
            return redirect(url_for("invoices"))
    elif new_status == "pending":
        invoice.status = "pending"
        flash(f"Invoice {invoice.invoice_number} marked as pending!", "success")
    
    db.session.commit()
    return redirect(url_for("invoices"))


@app.route("/invoices/delete/<int:invoice_id>")
@admin_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if not invoice.can_edit:
        flash("Cannot delete a paid or cancelled invoice", "danger")
        return redirect(url_for("invoices"))
    
    for item in invoice.items:
        product = Product.query.get(item.product_details)
        product.product_quantity += item.quantity
        record_stock_movement(item.product_details, 'return', item.quantity, 'invoice', invoice_id, notes="Invoice deleted")
    
    invoice_number = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()
    flash(f"Invoice {invoice_number} deleted successfully!", "success")
    return redirect(url_for("invoices"))


@app.route("/invoice/print/<int:invoice_id>")
@login_required
def invoice_print(invoice_id):
    invoice = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product)
    ).get_or_404(invoice_id)
    return render_template("print_invoice.html", invoice=invoice)


@app.route("/reports/sales")
@login_required
def sales_report():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    query = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product)
    ).filter(Invoice.status == 'paid')
    
    if start_date:
        query = query.filter(db.func.date(Invoice.created_at) >= start_date)
    if end_date:
        query = query.filter(db.func.date(Invoice.created_at) <= end_date)
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    total_sales = sum(inv.total for inv in invoices)
    total_tax = sum(inv.tax_amount for inv in invoices)
    total_discount = sum(inv.discount_amount for inv in invoices)
    
    return render_template("sales_report.html", 
                          invoices=invoices, 
                          total_sales=total_sales,
                          total_tax=total_tax,
                          total_discount=total_discount,
                          start_date=start_date,
                          end_date=end_date)


@app.route("/reports/stock")
@login_required
def stock_report():
    products = Product.query.filter_by(is_active=True).order_by(Product.product_quantity.asc()).all()
    total_value = sum(p.product_price * p.product_quantity for p in products)
    low_stock_count = sum(1 for p in products if p.is_low_stock)
    out_of_stock_count = sum(1 for p in products if p.product_quantity == 0)
    
    return render_template("stock_report.html",
                          products=products,
                          total_value=total_value,
                          low_stock_count=low_stock_count,
                          out_of_stock_count=out_of_stock_count)


if __name__ == "__main__":
    app.run(debug=True)
