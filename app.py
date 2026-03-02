import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from models import db, Customer, Product, Invoice, InvoiceItem

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'Zaq12wsX')
db_user = os.environ.get('DB_USER', 'postgres')
db_pass = os.environ.get('DB_PASSWORD', 'Zaq12wsX')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', '5432')
db_name = os.environ.get('DB_NAME', 'product')
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        db.drop_all()
    except:
        pass
    db.create_all()

    # Add sample data if tables are empty
    if Customer.query.count() == 0:
        # Sample customers
        customers = [
            Customer(first_name="John", last_name="Doe", phone_number="1234567890", customer_address="123 Main St"),
            Customer(first_name="Jane", last_name="Smith", phone_number="9876543210", customer_address="456 Oak Ave"),
            Customer(first_name="Bob", last_name="Johnson", phone_number="5551234567", customer_address="789 Pine Rd"),
        ]
        for c in customers:
            db.session.add(c)

        # Sample products
        products = [
            Product(product_type="Laptop", product_name="ThinkPad", product_model="T490", product_color="Black", product_price=999.99, product_quantity=10),
            Product(product_type="Phone", product_name="iPhone", product_model="14 Pro", product_color="Silver", product_price=1099.99, product_quantity=15),
            Product(product_type="Tablet", product_name="iPad", product_model="Air", product_color="Gold", product_price=599.99, product_quantity=8),
            Product(product_type="Monitor", product_name="Dell UltraSharp", product_model="U2720Q", product_color="Black", product_price=449.99, product_quantity=5),
            Product(product_type="Keyboard", product_name="Logitech MX", product_model="Master 3", product_color="Grey", product_price=99.99, product_quantity=20),
        ]
        for p in products:
            db.session.add(p)

        db.session.commit()


# Helper function to get cart
def get_cart():
    return session.get('cart', [])


def save_cart(cart):
    session['cart'] = cart


# -------- Home Page --------
@app.route("/")
def home():
    stats = {
        'customers': Customer.query.count(),
        'products': Product.query.count(),
        'invoices': Invoice.query.count()
    }
    return render_template("home.html", stats=stats)


# -------- Customers --------
@app.route("/customers")
def customers():
    return render_template("customers.html", customers=Customer.query.all())


@app.route("/customers/add", methods=["POST"])
def add_customer():
    first = request.form["first_name"]
    last = request.form["last_name"]
    phone = request.form["phone_number"]
    addr = request.form["customer_address"]
    db.session.add(Customer(first_name=first, last_name=last, phone_number=phone, customer_address=addr))
    db.session.commit()
    return redirect(url_for("customers"))


# -------- Products --------
@app.route("/products")
def products():
    return render_template("products.html", products=Product.query.all())


@app.route("/products/add", methods=["POST"])
def add_product():
    db.session.add(Product(
        product_type=request.form["product_type"],
        product_name=request.form["product_name"],
        product_model=request.form["product_model"],
        product_color=request.form["product_color"],
        product_price=float(request.form["product_price"]),
        product_quantity=int(request.form["product_quantity"])
    ))
    db.session.commit()
    return redirect(url_for("products"))


@app.route("/products/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        product.product_type = request.form["product_type"]
        product.product_name = request.form["product_name"]
        product.product_model = request.form["product_model"]
        product.product_color = request.form["product_color"]
        product.product_price = float(request.form["product_price"])
        product.product_quantity = int(request.form["product_quantity"])
        db.session.commit()
        return redirect(url_for("products"))
    return render_template("edit_product.html", product=product)


# -------- Cart --------
@app.route("/cart")
def cart():
    cart_items = get_cart()
    # Get product details for each cart item
    cart_products = []
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            cart_products.append({
                'product': product,
                'quantity': item['quantity']
            })
    return render_template("cart.html", cart_products=cart_products, customers=Customer.query.all())


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def cart_add(product_id):
    quantity = int(request.form.get('quantity', 1))
    product = Product.query.get_or_404(product_id)

    cart = get_cart()

    # Check if product already in cart
    for item in cart:
        if item['product_id'] == product_id:
            # Check total stock
            total = item['quantity'] + quantity
            if total > product.product_quantity:
                flash(f"Insufficient stock! Available: {product.product_quantity}", "danger")
            else:
                item['quantity'] = total
                save_cart(cart)
                flash(f"Updated {product.product_name} quantity in cart", "success")
            return redirect(url_for("cart"))

    # Check stock before adding
    if quantity > product.product_quantity:
        flash(f"Insufficient stock! Available: {product.product_quantity}", "danger")
        return redirect(url_for("invoices"))

    cart.append({'product_id': product_id, 'quantity': quantity})
    save_cart(cart)
    flash(f"Added {product.product_name} to cart", "success")
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:product_id>")
def cart_remove(product_id):
    cart = get_cart()
    cart = [item for item in cart if item['product_id'] != product_id]
    save_cart(cart)
    flash("Item removed from cart", "success")
    return redirect(url_for("cart"))


@app.route("/cart/update/<int:product_id>", methods=["POST"])
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
def cart_clear():
    save_cart([])
    flash("Cart cleared", "success")
    return redirect(url_for("cart"))


@app.route("/cart/checkout", methods=["POST"])
def cart_checkout():
    customer_id = int(request.form["customer_id"])
    cart = get_cart()

    if not cart:
        flash("Cart is empty", "warning")
        return redirect(url_for("invoices"))

    # Verify all products have sufficient stock
    for item in cart:
        product = Product.query.get(item['product_id'])
        if not product or product.product_quantity < item['quantity']:
            flash(f"Insufficient stock for {product.product_name if product else 'product'}", "danger")
            return redirect(url_for("cart"))

    # Create single invoice with multiple items
    invoice = Invoice(customer_details=customer_id)
    db.session.add(invoice)
    db.session.flush()  # Get invoice_id

    # Create invoice items
    for item in cart:
        product = Product.query.get(item['product_id'])
        db.session.add(InvoiceItem(
            invoice_id=invoice.invoice_id,
            product_details=item['product_id'],
            quantity=item['quantity'],
            unit_price=product.product_price
        ))
        # Deduct stock
        product.product_quantity -= item['quantity']

    db.session.commit()
    save_cart([])
    flash("Invoice created successfully!", "success")
    return redirect(url_for("invoice_print", invoice_id=invoice.invoice_id))


# -------- Invoices --------
@app.route("/invoices")
def invoices():
    available_products = Product.query.filter(Product.product_quantity > 0).all()
    invoices_list = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product)
    ).all()
    cart_count = len(get_cart())
    return render_template("invoices.html", invoices=invoices_list, customers=Customer.query.all(), products=available_products, cart_count=cart_count)


# -------- Print Invoice --------
@app.route("/invoice/print/<int:invoice_id>")
def invoice_print(invoice_id):
    invoice = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product)
    ).get_or_404(invoice_id)
    return render_template("print_invoice.html", invoice=invoice)


if __name__ == "__main__":
    app.run(debug=True)
