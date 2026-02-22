from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from models import db, Customer, Product, Invoice

app = Flask(__name__)
app.config['SECRET_KEY'] = "Zaq12wsX"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:Zaq12wsX@localhost:5432/product"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.drop_all()
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


# -------- Invoices --------
@app.route("/invoices")
def invoices():
    # Only show products with quantity > 0
    available_products = Product.query.filter(Product.product_quantity > 0).all()
    invoices_list = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.product)
    ).all()
    return render_template("invoices.html", invoices=invoices_list, customers=Customer.query.all(), products=available_products)


@app.route("/invoices/add", methods=["POST"])
def add_invoice():
    product_id = int(request.form["product_id"])
    customer_id = int(request.form["customer_id"])
    quantity = int(request.form["quantity"])

    # Get product and check stock
    product = Product.query.get(product_id)
    if product.product_quantity < quantity:
        flash(f"Insufficient stock! Available: {product.product_quantity}", "danger")
        return redirect(url_for("invoices"))

    # Create invoice
    db.session.add(Invoice(
        product_details=product_id,
        customer_details=customer_id,
        quantity=quantity
    ))

    # Deduct from stock
    product.product_quantity -= quantity
    db.session.commit()

    return redirect(url_for("invoices"))


if __name__ == "__main__":
    app.run(debug=True)
