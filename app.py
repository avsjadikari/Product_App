from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from models import db, Customer, Product, Invoice

app = Flask(__name__)
app.config['SECRET_KEY'] = "Zaq12wsX"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:Zaq12wsX@localhost:5432/product"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


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
        product_color=request.form["product_color"],
        product_price=float(request.form["product_price"])
    ))
    db.session.commit()
    return redirect(url_for("products"))


# -------- Invoices --------
@app.route("/invoices")
def invoices():
    # Use eager loading to prevent N+1 query problem
    invoices_list = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.product)
    ).all()
    return render_template("invoices.html", invoices=invoices_list, customers=Customer.query.all(), products=Product.query.all())


@app.route("/invoices/add", methods=["POST"])
def add_invoice():
    db.session.add(Invoice(
        product_details=request.form["product_id"],
        customer_details=request.form["customer_id"],
        quantity=int(request.form["quantity"])
    ))
    db.session.commit()
    return redirect(url_for("invoices"))


if __name__ == "__main__":
    app.run(debug=True)
