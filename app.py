import os
import re
import logging
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import quote_plus

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import joinedload
from flask_migrate import Migrate

from models import db, User, Customer, Product, Invoice, InvoiceItem, StockMovement
from config import Config
from forms import (
    LoginForm,
    CustomerForm,
    ProductForm,
    UserForm,
    ChangePasswordForm,
    InvoiceForm,
    InvoiceItemForm,
    StockAdjustForm,
    CheckoutForm,
    CartUpdateForm,
    InvoiceStatusForm,
    CartAddForm,
    SetupForm,
)
from api import api as api_blueprint
from utils import (
    export_products_csv,
    export_customers_csv,
    export_invoices_csv,
    export_sales_report_csv,
    search_products,
    search_customers,
    search_invoices,
)

app = Flask(__name__)

# Always check fresh config at runtime
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Load config.json at startup if it exists
config_file = Path(__file__).parent / "config.json"
if config_file.exists():
    import json

    with open(config_file, "r") as f:
        config = json.load(f)
    if config.get("DB_HOST") and config.get("DB_NAME"):
        user = config.get("DB_USER", "postgres")
        password = config.get("DB_PASSWORD", "") or ""
        host = config.get("DB_HOST", "localhost")
        port = config.get("DB_PORT", "5432")
        name = config.get("DB_NAME", "product")
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}"
        )
        app.config["SECRET_KEY"] = config.get("SECRET_KEY", "dev-key")
        app.config["WTF_CSRF_ENABLED"] = True
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost:5432/postgres"
        app.config["SECRET_KEY"] = "temp-secret-key-for-setup"
        app.config["WTF_CSRF_ENABLED"] = False
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost:5432/postgres"
    app.config["SECRET_KEY"] = "temp-secret-key-for-setup"
    app.config["WTF_CSRF_ENABLED"] = False

# Register API blueprint
app.register_blueprint(api_blueprint)

# Initialize DB - will be reconfigured on each request
db.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

app_logger = logging.getLogger(__name__)

# Initialize _last_config_uri from startup config
config_file = Path(__file__).parent / "config.json"
_last_config_uri = None
if config_file.exists():
    import json

    with open(config_file, "r") as f:
        config = json.load(f)
    if config.get("DB_HOST") and config.get("DB_NAME"):
        user = config.get("DB_USER", "postgres")
        password = config.get("DB_PASSWORD", "") or ""
        host = config.get("DB_HOST", "localhost")
        port = config.get("DB_PORT", "5432")
        name = config.get("DB_NAME", "product")
        _last_config_uri = f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}"


@app.before_request
def before_request():
    """Reconfigure database before each request if config exists."""
    global _last_config_uri

    config_file = Path(__file__).parent / "config.json"
    if config_file.exists():
        import json

        with open(config_file, "r") as f:
            config = json.load(f)
        if config.get("DB_HOST") and config.get("DB_NAME"):
            user = config.get("DB_USER", "postgres")
            password = config.get("DB_PASSWORD", "")
            host = config.get("DB_HOST", "localhost")
            port = config.get("DB_PORT", "5432")
            name = config.get("DB_NAME", "product")
            uri = f"postgresql://{user}:{password}@{host}:{port}/{name}"

            if uri != _last_config_uri:
                _last_config_uri = uri
                db.engine.dispose()
                app.config["SQLALCHEMY_DATABASE_URI"] = uri
                app.config["SECRET_KEY"] = config.get("SECRET_KEY", "dev-key")
                app.config["WTF_CSRF_ENABLED"] = True


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password meets security requirements."""
    if len(password) < Config.PASSWORD_MIN_LENGTH:
        return (
            False,
            f"Password must be at least {Config.PASSWORD_MIN_LENGTH} characters",
        )

    if Config.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if Config.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if Config.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if Config.PASSWORD_REQUIRE_SPECIAL and not re.search(
        r'[!@#$%^&*(),.?":{}|<>]', password
    ):
        return False, "Password must contain at least one special character"

    return True, ""


def log_user_action(action: str, details: Optional[str] = None) -> None:
    """Log user actions for audit trail."""
    username = session.get("username", "Anonymous")
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent", "Unknown")

    log_msg = f"USER: {username} | ACTION: {action} | IP: {ip_address}"
    if details:
        log_msg += f" | DETAILS: {details}"

    app_logger.info(log_msg)


def log_error(error_type: str, error_message: str) -> None:
    """Log errors for debugging and monitoring."""
    username = session.get("username", "Anonymous")
    app_logger.error(
        f"USER: {username} | ERROR: {error_type} | MESSAGE: {error_message}"
    )


def audit_required(action_name: str):
    """Decorator to audit specific actions."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            log_user_action(action_name)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user() -> Optional[User]:
    if "user_id" in session:
        return db.session.get(User, session["user_id"])
    return None


def sanitize_search_input(search_term: Any) -> str:
    """Sanitize search input to prevent abuse."""
    if not search_term:
        return ""
    max_length = Config.MAX_SEARCH_LENGTH
    sanitized = str(search_term)[:max_length].strip()
    return sanitized


login_attempts: dict = {}


def check_rate_limit(ip_address: str) -> bool:
    """Check if IP has exceeded login attempts."""
    import time

    current_time = time.time()
    window = Config.LOGIN_RATE_LIMIT

    if ip_address not in login_attempts:
        login_attempts[ip_address] = []

    login_attempts[ip_address] = [
        t
        for t in login_attempts[ip_address]
        if current_time - t < Config.LOGIN_RATE_WINDOW
    ]

    if len(login_attempts[ip_address]) >= Config.LOGIN_RATE_LIMIT:
        return False

    login_attempts[ip_address].append(current_time)
    return True


@app.context_processor
def inject_user() -> dict:
    return dict(current_user=get_current_user(), request=request)


def create_sample_data() -> None:
    """Create sample data for initial database setup."""
    admin = User(
        username=Config.DEFAULT_ADMIN_USER, role="admin", force_password_change=True
    )
    admin.set_password(Config.DEFAULT_ADMIN_PASSWORD)
    db.session.add(admin)

    user = User(username=Config.DEFAULT_USER_USER, role="user")
    user.set_password(Config.DEFAULT_USER_PASSWORD)
    db.session.add(user)

    customers = [
        Customer(
            first_name="John",
            last_name="Doe",
            phone_number="1234567890",
            customer_address="123 Main St",
            email="john@example.com",
        ),
        Customer(
            first_name="Jane",
            last_name="Smith",
            phone_number="9876543210",
            customer_address="456 Oak Ave",
            email="jane@example.com",
        ),
        Customer(
            first_name="Bob",
            last_name="Johnson",
            phone_number="5551234567",
            customer_address="789 Pine Rd",
            email="bob@example.com",
        ),
    ]
    for c in customers:
        db.session.add(c)

    products = [
        Product(
            product_type="Laptop",
            product_name="ThinkPad",
            product_model="T490",
            product_color="Black",
            product_price=999.99,
            product_quantity=10,
            low_stock_threshold=5,
        ),
        Product(
            product_type="Phone",
            product_name="iPhone",
            product_model="14 Pro",
            product_color="Silver",
            product_price=1099.99,
            product_quantity=15,
            low_stock_threshold=5,
        ),
        Product(
            product_type="Tablet",
            product_name="iPad",
            product_model="Air",
            product_color="Gold",
            product_price=599.99,
            product_quantity=8,
            low_stock_threshold=5,
        ),
        Product(
            product_type="Monitor",
            product_name="Dell UltraSharp",
            product_model="U2720Q",
            product_color="Black",
            product_price=449.99,
            product_quantity=5,
            low_stock_threshold=3,
        ),
        Product(
            product_type="Keyboard",
            product_name="Logitech MX",
            product_model="Master 3",
            product_color="Grey",
            product_price=99.99,
            product_quantity=20,
            low_stock_threshold=5,
        ),
    ]
    for p in products:
        db.session.add(p)

    db.session.commit()


def init_database():
    """Initialize database and create sample data if needed."""
    if not Config.is_configured():
        return

    with app.app_context():
        try:
            db.create_all()
            if User.query.count() == 0:
                create_sample_data()
                app_logger.info("Sample data created successfully")
        except Exception as e:
            app_logger.error(f"Database initialization error: {str(e)}")


init_database()


def get_cart() -> list:
    return session.get("cart", [])


def save_cart(cart: list) -> None:
    session["cart"] = cart


def record_stock_movement(
    product_id: int,
    movement_type: str,
    quantity: int,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    notes: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Optional[StockMovement]:
    try:
        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            created_by=created_by,
        )
        db.session.add(movement)
        db.session.flush()
        return movement
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Stock movement error: {str(e)}")
        return None


def update_stock(
    product_id: int,
    quantity_change: int,
    movement_type: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> Tuple[bool, str]:
    try:
        product = Product.query.get_or_404(product_id)
        new_quantity = product.product_quantity + quantity_change

        if new_quantity < 0:
            return (
                False,
                f"Insufficient stock for {product.product_name}. Available: {product.product_quantity}",
            )

        product.product_quantity = new_quantity
        record_stock_movement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=abs(quantity_change),
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
        )
        db.session.commit()
        return True, "Stock updated successfully"
    except Exception as e:
        db.session.rollback()
        app_logger.error(f"Stock update error: {str(e)}")
        return False, f"Error updating stock: {str(e)}"


def safe_int_convert(value: Any, default: int = 0) -> int:
    """Safely convert input to integer."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float_convert(value: Any, default: float = 0.0) -> float:
    """Safely convert input to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@app.route("/setup", methods=["GET", "POST"])
def setup():
    """Database setup wizard."""
    if Config.is_configured():
        return redirect(url_for("login"))

    # Handle both form submission and direct POST
    if request.method == "POST":
        db_host = request.form.get("db_host", "").strip()
        db_port = request.form.get("db_port", "").strip()
        db_name = request.form.get("db_name", "").strip()
        db_user = request.form.get("db_user", "").strip()
        db_password = request.form.get("db_password", "")
        secret_key = request.form.get("secret_key", "").strip()

        # Validate required fields
        if not all([db_host, db_port, db_name, db_user, secret_key]):
            flash("All fields are required.", "danger")
            current_config = Config.get_current_config()
            return render_template(
                "setup.html", config=current_config, form=SetupForm()
            )

        config_data = {
            "DB_HOST": db_host,
            "DB_PORT": db_port,
            "DB_NAME": db_name,
            "DB_USER": db_user,
            "DB_PASSWORD": db_password,
            "SECRET_KEY": secret_key,
        }

        if Config.save_config(config_data):
            # Update the URI BEFORE disposing the old engine
            new_uri = f"postgresql://{quote_plus(db_user)}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"
            app.config["SQLALCHEMY_DATABASE_URI"] = new_uri
            app.config["SECRET_KEY"] = secret_key
            app.config["WTF_CSRF_ENABLED"] = True

            # Dispose old engine and create new one
            db.engine.dispose()

            # Initialize database
            try:
                # First create the database if it doesn't exist
                from sqlalchemy import create_engine, text

                # Validate database name to prevent SQL injection
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", db_name):
                    flash(
                        "Invalid database name. Use only alphanumeric characters and underscores.",
                        "danger",
                    )
                    return redirect(url_for("setup"))

                temp_uri = f"postgresql://{quote_plus(db_user)}:{quote_plus(db_password)}@{db_host}:{db_port}/postgres"
                temp_engine = create_engine(temp_uri)
                with temp_engine.connect() as conn:
                    # Use parameterized query for SELECT
                    result = conn.execute(
                        text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                        {"db_name": db_name},
                    )
                    if result.fetchone() is None:
                        # CREATE DATABASE cannot use parameterized queries, but we validated the name
                        conn.execute(text(f"CREATE DATABASE {db_name}"))
                temp_engine.dispose()

                # Now create tables in the new database
                db.create_all()
                if User.query.count() == 0:
                    create_sample_data()
                flash("Configuration saved and database initialized!", "success")
                return redirect(url_for("login"))
            except Exception as e:
                flash(f"Database connection failed: {str(e)}", "danger")
        else:
            flash("Failed to save configuration.", "danger")

    current_config = Config.get_current_config()
    return render_template("setup.html", config=current_config, form=SetupForm())


@app.route("/setup/test-connection", methods=["POST"])
def test_db_connection():
    """Test database connection."""
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError

    db_host = request.form.get("db_host", "").strip()
    db_port = request.form.get("db_port", "").strip()
    db_name = request.form.get("db_name", "").strip()
    db_user = request.form.get("db_user", "").strip()
    db_password = request.form.get("db_password", "")

    if not all([db_host, db_port, db_name, db_user]):
        return jsonify(
            {"success": False, "message": "All fields except password are required."}
        )

    try:
        test_uri = f"postgresql://{quote_plus(db_user)}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(test_uri)
        conn = engine.connect()
        conn.close()
        engine.dispose()
        return jsonify({"success": True, "message": "Connection successful!"})
    except OperationalError as e:
        return jsonify({"success": False, "message": f"Connection failed: {str(e)}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@app.route("/login", methods=["GET", "POST"])
def login():
    if not Config.is_configured():
        return redirect(url_for("setup"))

    form = LoginForm()
    if request.method == "POST":
        if not check_rate_limit(request.remote_addr):
            flash("Too many login attempts. Please try again later.", "danger")
            return redirect(url_for("login"))

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        remember_me = request.form.get("remember_me") == "on"

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("login"))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            session["user_id"] = user.user_id
            session["username"] = user.username
            session["role"] = user.role

            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(hours=1)

            log_user_action("LOGIN", f"User {username} logged in successfully")

            if user.force_password_change:
                flash("You must change your password before continuing.", "warning")
                return redirect(url_for("change_password"))

            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.", "danger")
            log_user_action(
                "LOGIN_FAILED", f"Failed login attempt for username: {username}"
            )

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    username = session.get("username", "Unknown")
    session.clear()
    log_user_action("LOGOUT", f"User {username} logged out")
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    user = db.session.get(User, session["user_id"])
    form = ChangePasswordForm()

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("change_password"))

        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            flash(error_msg, "danger")
            return redirect(url_for("change_password"))

        user.set_password(new_password)
        user.force_password_change = False
        db.session.commit()
        flash("Password changed successfully!", "success")
        return redirect(url_for("home"))

    return render_template("change_password.html", user=user, form=form)


@app.route("/")
def index():
    """Redirect to setup if not configured, otherwise to home."""
    try:
        if not Config.is_configured():
            return redirect(url_for("setup"))
        if "user_id" not in session:
            return redirect(url_for("login"))
        return redirect(url_for("home"))
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/home")
@login_required
def home():
    stats = {
        "customers": Customer.query.filter_by(is_active=True).count(),
        "products": Product.query.filter_by(is_active=True).count(),
        "invoices": Invoice.query.count(),
        "pending_invoices": Invoice.query.filter_by(status="pending").count(),
        "paid_invoices": Invoice.query.filter_by(status="paid").count(),
    }
    low_stock_products = Product.query.filter(
        Product.product_quantity <= Product.low_stock_threshold,
        Product.is_active == True,
    ).all()
    recent_invoices = (
        Invoice.query.options(joinedload(Invoice.customer))
        .order_by(Invoice.created_at.desc())
        .limit(5)
        .all()
    )

    total_revenue = (
        db.session.query(db.func.sum(Invoice.total))
        .filter(Invoice.status == "paid")
        .scalar()
        or 0
    )

    today = datetime.now()
    seven_days_ago = today - timedelta(days=6)

    sales_data = (
        db.session.query(
            db.func.date(Invoice.created_at).label("date"),
            db.func.sum(Invoice.total).label("total"),
        )
        .filter(Invoice.status == "paid", Invoice.created_at >= seven_days_ago)
        .group_by(db.func.date(Invoice.created_at))
        .order_by(db.func.date(Invoice.created_at))
        .all()
    )

    sales_dict = {}
    for data_date, data_total in sales_data:
        date_str = str(data_date).split(" ")[0]
        sales_dict[date_str] = data_total

    chart_labels = []
    chart_data = []
    for idx in range(7):
        day = (seven_days_ago + timedelta(days=idx)).date()
        date_str = day.strftime("%Y-%m-%d")
        chart_labels.append(day.strftime("%b %d"))
        chart_data.append(float(sales_dict.get(date_str, 0)))

    return render_template(
        "home.html",
        stats=stats,
        low_stock_products=low_stock_products,
        recent_invoices=recent_invoices,
        total_revenue=total_revenue,
        chart_labels=chart_labels,
        chart_data=chart_data,
    )


@app.route("/audit-logs")
@admin_required
def audit_logs():
    """Display audit logs from the log file."""
    from datetime import datetime, timedelta
    from pathlib import Path

    date_range = request.args.get("date_range", "7days")
    action_type = request.args.get("action_type", "")
    user_filter = request.args.get("user", "")

    log_file = Path(__file__).parent / "logs" / "app.log"
    logs = []

    date_range_labels = {
        "today": "Today",
        "7days": "Last 7 Days",
        "30days": "Last 30 Days",
        "all": "All Time"
    }
    date_range_label = date_range_labels.get(date_range, "All Time")

    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "USER:" not in line:
                        continue

                    parts = line.strip().split(" | ")
                    if len(parts) < 5:
                        continue

                    try:
                        timestamp_str = parts[0]
                        log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue

                    if date_range != "all":
                        now = datetime.now()
                        if date_range == "today":
                            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        elif date_range == "7days":
                            start_date = now - timedelta(days=7)
                        elif date_range == "30days":
                            start_date = now - timedelta(days=30)
                        else:
                            start_date = datetime.min

                        if log_time < start_date:
                            continue

                    user_part = parts[3] if len(parts) > 3 else ""
                    user = user_part.replace("USER: ", "") if "USER:" in user_part else "Unknown"

                    action_part = parts[4] if len(parts) > 4 else ""
                    action = action_part.replace("ACTION: ", "") if "ACTION:" in action_part else "Unknown"

                    ip_part = parts[5] if len(parts) > 5 else ""
                    ip = ip_part.replace("IP: ", "") if "IP:" in ip_part else "Unknown"

                    details = ""
                    if "DETAILS:" in line:
                        details_part = line.split("DETAILS: ")[1].strip() if "DETAILS: " in line else ""
                        details = details_part

                    if action_type and action_type not in action:
                        continue
                    if user_filter and user_filter != user:
                        continue

                    logs.append({
                        "timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "username": user,
                        "action": action,
                        "ip": ip,
                        "details": details
                    })

        except Exception as e:
            app_logger.error(f"Error reading audit logs: {str(e)}")

    logs.reverse()

    users = User.query.all()

    return render_template(
        "audit_logs.html",
        logs=logs[:200],
        users=users,
        date_range=date_range,
        action_type=action_type,
        user_filter=user_filter,
        date_range_label=date_range_label
    )


@app.route("/users")
@admin_required
def users():
    return render_template("users.html", users=User.query.all())


@app.route("/users/add", methods=["POST"])
@admin_required
def add_user():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    role = request.form.get("role", "user")

    if not username or not password:
        flash("Username and password are required.", "danger")
        return redirect(url_for("users"))

    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "danger")
        return redirect(url_for("users"))

    is_valid, error_msg = validate_password(password)
    if not is_valid:
        flash(f"Password error: {error_msg}", "danger")
        return redirect(url_for("users"))

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f"User {username} created successfully!", "success")
    return redirect(url_for("users"))


@app.route("/users/delete/<int:id>")
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.user_id == session.get("user_id"):
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("users"))
    username = user.username
    user.is_active = False
    db.session.commit()
    flash(f"User {username} deleted successfully!", "success")
    return redirect(url_for("users"))


@app.route("/database/reset", methods=["POST"])
@admin_required
@csrf.exempt
def reset_database():
    try:
        db.drop_all()
        db.create_all()
        create_sample_data()
        session.clear()
        flash(
            "Database reset successfully! Please login with default credentials and change your password.",
            "success",
        )
    except Exception as e:
        flash(f"Error resetting database: {str(e)}", "danger")

    return redirect(url_for("login"))


@app.route("/customers")
@login_required
def customers():
    form = CustomerForm()
    search = sanitize_search_input(request.args.get("search", ""))
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Customer.query.filter_by(is_active=True)

    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Customer.first_name.ilike(term),
                Customer.last_name.ilike(term),
                Customer.phone_number.ilike(term),
                Customer.email.ilike(term),
            )
        )

    pagination = query.order_by(Customer.first_name, Customer.last_name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "customers.html",
        customers=pagination.items,
        pagination=pagination,
        search=search,
        form=form,
    )


@app.route("/customers/add", methods=["POST"])
@login_required
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        try:
            customer = Customer(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone_number=form.phone_number.data,
                customer_address=form.customer_address.data,
                email=form.email.data,
            )
            db.session.add(customer)
            db.session.commit()
            log_user_action("CUSTOMER_CREATE", f"Created customer: {customer.full_name}")
            flash("Customer added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            log_error("ADD_CUSTOMER", str(e))
            flash(f"Error adding customer: {str(e)}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")
    return redirect(url_for("customers"))


@app.route("/customers/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        form.populate_obj(customer)
        db.session.commit()
        log_user_action("CUSTOMER_UPDATE", f"Updated customer: {customer.full_name}")
        flash("Customer updated successfully!", "success")
        return redirect(url_for("customers"))
    return render_template("edit_customer.html", customer=customer, form=form)


@app.route("/customers/view/<int:id>")
@login_required
def view_customer(id):
    customer = Customer.query.options(joinedload(Customer.invoices)).get_or_404(id)

    lifetime_value = sum(inv.total for inv in customer.invoices if inv.status == "paid")

    return render_template(
        "customer_profile.html", customer=customer, lifetime_value=lifetime_value
    )


@app.route("/customers/delete/<int:id>")
@admin_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    customer_name = customer.full_name
    customer.is_active = False
    db.session.commit()
    log_user_action("CUSTOMER_DELETE", f"Deleted customer: {customer_name}")
    flash("Customer deleted successfully!", "success")
    return redirect(url_for("customers"))


@app.route("/products")
@login_required
def products():
    form = ProductForm()
    search = sanitize_search_input(request.args.get("search", ""))
    product_type = sanitize_search_input(request.args.get("type", ""))
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Product.query.filter_by(is_active=True)

    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.product_name.ilike(term),
                Product.product_model.ilike(term),
                Product.product_type.ilike(term),
                Product.product_color.ilike(term),
            )
        )

    if product_type:
        query = query.filter_by(product_type=product_type)

    product_types = db.session.query(Product.product_type).distinct().all()
    product_types = [pt[0] for pt in product_types]

    pagination = query.order_by(Product.product_name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "products.html",
        products=pagination.items,
        pagination=pagination,
        search=search,
        selected_type=product_type,
        product_types=product_types,
        form=form,
    )


@app.route("/products/add", methods=["POST"])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        try:
            product = Product(
                product_type=form.product_type.data,
                product_name=form.product_name.data,
                product_model=form.product_model.data,
                product_color=form.product_color.data,
                product_price=form.product_price.data,
                product_quantity=form.product_quantity.data,
                low_stock_threshold=form.low_stock_threshold.data or 5,
            )
            db.session.add(product)
            db.session.commit()
            log_user_action("PRODUCT_CREATE", f"Created product: {product.product_name} ({product.product_model})")
            flash("Product added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            log_error("ADD_PRODUCT", str(e))
            flash(f"Error adding product: {str(e)}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "danger")
    return redirect(url_for("products"))


@app.route("/products/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        old_quantity = product.product_quantity
        old_name = product.product_name
        form.populate_obj(product)

        new_quantity = form.product_quantity.data
        if new_quantity != old_quantity:
            quantity_diff = new_quantity - old_quantity
            if quantity_diff > 0:
                record_stock_movement(
                    product.product_id,
                    "adjustment_in",
                    quantity_diff,
                    notes="Product edit adjustment",
                )
            else:
                record_stock_movement(
                    product.product_id,
                    "adjustment_out",
                    abs(quantity_diff),
                    notes="Product edit adjustment",
                )

        db.session.commit()
        log_user_action("PRODUCT_UPDATE", f"Updated product: {old_name} -> {product.product_name}, qty: {old_quantity} -> {new_quantity}")
        flash("Product updated successfully!", "success")
        return redirect(url_for("products"))
    return render_template("edit_product.html", product=product, form=form)


@app.route("/products/delete/<int:id>")
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    product_name = product.product_name
    product.is_active = False
    db.session.commit()
    log_user_action("PRODUCT_DELETE", f"Deleted product: {product_name}")
    flash("Product deleted successfully!", "success")
    return redirect(url_for("products"))


@app.route("/stock")
@login_required
def stock_management():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    products = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.product_quantity.asc())
        .all()
    )

    pagination = StockMovement.query.order_by(StockMovement.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template(
        "stock.html",
        products=products,
        movements=pagination.items,
        pagination=pagination,
    )


@app.route("/stock/adjust", methods=["POST"])
@login_required
def stock_adjust():
    product_id = safe_int_convert(request.form.get("product_id"))
    adjustment = safe_int_convert(request.form.get("quantity"))
    notes = request.form.get("notes", "")

    if product_id <= 0:
        flash("Invalid product selected.", "danger")
        return redirect(url_for("stock_management"))

    if adjustment == 0:
        flash("Quantity adjustment cannot be zero.", "danger")
        return redirect(url_for("stock_management"))

    product = db.session.get(Product, product_id)
    product_name = product.product_name if product else "Unknown"

    success, message = update_stock(
        product_id=product_id,
        quantity_change=adjustment,
        movement_type="adjustment_in" if adjustment > 0 else "adjustment_out",
        reference_type="manual",
        notes=notes,
    )

    if success:
        action_type = "STOCK_IN" if adjustment > 0 else "STOCK_OUT"
        log_user_action(action_type, f"Stock {action_type.replace('_', ' ').lower()}: {product_name}, qty: {adjustment}")
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
        product = db.session.get(Product, item["product_id"])
        if product:
            cart_products.append({"product": product, "quantity": item["quantity"]})
    return render_template(
        "cart.html",
        cart_products=cart_products,
        customers=Customer.query.filter_by(is_active=True).all(),
    )


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def cart_add(product_id):
    quantity = safe_int_convert(request.form.get("quantity", 1))
    product = Product.query.get_or_404(product_id)
    cart = get_cart()

    if quantity < 1:
        flash("Quantity must be at least 1.", "danger")
        return redirect(url_for("cart"))

    for item in cart:
        if item["product_id"] == product_id:
            total = item["quantity"] + quantity
            if total > product.product_quantity:
                flash(
                    f"Insufficient stock! Available: {product.product_quantity}",
                    "danger",
                )
            else:
                item["quantity"] = total
                save_cart(cart)
                log_user_action("CART_UPDATE", f"Updated cart: {product.product_name}, qty: {total}")
                flash(f"Updated {product.product_name} quantity in cart", "success")
            return redirect(url_for("cart"))

    if quantity > product.product_quantity:
        flash(f"Insufficient stock! Available: {product.product_quantity}", "danger")
        return redirect(url_for("invoices"))

    cart.append({"product_id": product_id, "quantity": quantity})
    save_cart(cart)
    log_user_action("CART_ADD", f"Added to cart: {product.product_name}, qty: {quantity}")
    flash(f"Added {product.product_name} to cart", "success")
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:product_id>")
@login_required
@csrf.exempt
def cart_remove(product_id):
    cart = get_cart()
    product = db.session.get(Product, product_id)
    product_name = product.product_name if product else f"Product ID {product_id}"
    cart = [item for item in cart if item["product_id"] != product_id]
    save_cart(cart)
    log_user_action("CART_REMOVE", f"Removed from cart: {product_name}")
    flash("Item removed from cart", "success")
    return redirect(url_for("cart"))


@app.route("/cart/update/<int:product_id>", methods=["POST"])
@login_required
def cart_update(product_id):
    quantity = safe_int_convert(request.form.get("quantity", 1))
    product = Product.query.get_or_404(product_id)
    cart = get_cart()

    if quantity < 1:
        flash("Quantity must be at least 1.", "danger")
        return redirect(url_for("cart"))

    for item in cart:
        if item["product_id"] == product_id:
            if quantity > product.product_quantity + item["quantity"]:
                flash(
                    f"Insufficient stock! Available: {product.product_quantity + item['quantity']}",
                    "danger",
                )
            else:
                item["quantity"] = quantity
                save_cart(cart)
                log_user_action("CART_UPDATE", f"Updated cart: {product.product_name}, qty: {quantity}")
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
    customer_id = safe_int_convert(request.form.get("customer_id"))
    tax_rate = safe_float_convert(request.form.get("tax_rate", 0))
    discount_amount = safe_float_convert(request.form.get("discount_amount", 0))
    cart = get_cart()

    if not cart:
        flash("Cart is empty", "warning")
        return redirect(url_for("invoices"))

    if customer_id <= 0:
        flash("Invalid customer selected.", "danger")
        return redirect(url_for("cart"))

    for item in cart:
        product = db.session.get(Product, item["product_id"])
        if not product or product.product_quantity < item["quantity"]:
            flash(
                f"Insufficient stock for {product.product_name if product else 'product'}",
                "danger",
            )
            return redirect(url_for("cart"))

    try:
        invoice = Invoice(
            customer_details=customer_id,
            invoice_number=Invoice.generate_invoice_number(),
            status="pending",
            tax_rate=tax_rate,
            discount_amount=discount_amount,
        )
        db.session.add(invoice)
        db.session.flush()

        for item in cart:
            product = db.session.get(Product, item["product_id"])
            invoice_item = InvoiceItem(
                invoice_id=invoice.invoice_id,
                product_details=item["product_id"],
                quantity=item["quantity"],
                unit_price=product.product_price,
            )
            invoice_item.calculate_total()
            db.session.add(invoice_item)

            product.product_quantity -= item["quantity"]
            record_stock_movement(
                product_id=item["product_id"],
                movement_type="sale",
                quantity=item["quantity"],
                reference_type="invoice",
                reference_id=invoice.invoice_id,
            )

        invoice.calculate_totals()
        db.session.commit()
        customer = db.session.get(Customer, customer_id)
        customer_name = customer.full_name if customer else f"Customer ID {customer_id}"
        item_count = len(cart)
        total_items = sum(item["quantity"] for item in cart)
        log_user_action("INVOICE_CREATE", f"Created invoice: {invoice.invoice_number}, customer: {customer_name}, items: {item_count}, qty: {total_items}, total: {invoice.total}")
        save_cart([])
        flash(f"Invoice {invoice.invoice_number} created successfully!", "success")
        return redirect(url_for("invoice_print", invoice_id=invoice.invoice_id))
    except Exception as e:
        db.session.rollback()
        log_error("CHECKOUT_ERROR", str(e))
        flash(f"Error processing checkout: {str(e)}", "danger")
        return redirect(url_for("cart"))


@app.route("/invoices")
@login_required
def invoices():
    status_filter = request.args.get("status", "all")
    search = sanitize_search_input(request.args.get("search", ""))
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product),
    )

    if status_filter != "all":
        query = query.filter(Invoice.status == status_filter)

    if search:
        term = f"%{search}%"
        query = query.join(Customer).filter(
            db.or_(
                Invoice.invoice_number.ilike(term),
                Customer.first_name.ilike(term),
                Customer.last_name.ilike(term),
            )
        )

    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    available_products = Product.query.filter(
        Product.product_quantity > 0, Product.is_active == True
    ).all()

    return render_template(
        "invoices.html",
        invoices=pagination.items,
        customers=Customer.query.filter_by(is_active=True).all(),
        products=available_products,
        cart_count=len(get_cart()),
        current_status=status_filter,
        pagination=pagination,
        search=search,
    )


@app.route("/invoices/create", methods=["POST"])
@login_required
def create_invoice():
    customer_id = safe_int_convert(request.form.get("customer_id"))

    if customer_id <= 0:
        flash("Invalid customer selected.", "danger")
        return redirect(url_for("invoices"))

    invoice = Invoice(
        customer_details=customer_id,
        invoice_number=Invoice.generate_invoice_number(),
        status="draft",
    )
    db.session.add(invoice)
    db.session.flush()
    return redirect(url_for("edit_invoice", invoice_id=invoice.invoice_id))


@app.route("/invoices/edit/<int:invoice_id>", methods=["GET", "POST"])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product),
    ).get_or_404(invoice_id)

    if not invoice.can_edit:
        flash("Cannot edit a paid or cancelled invoice", "danger")
        return redirect(url_for("invoices"))

    if request.method == "POST":
        invoice.tax_rate = safe_float_convert(request.form.get("tax_rate", 0))
        invoice.discount_amount = safe_float_convert(
            request.form.get("discount_amount", 0)
        )
        invoice.notes = request.form.get("notes", "")[:1000]
        invoice.calculate_totals()
        db.session.commit()
        flash("Invoice updated!", "success")
        return redirect(url_for("edit_invoice", invoice_id=invoice_id))

    available_products = Product.query.filter(
        Product.product_quantity > 0, Product.is_active == True
    ).all()
    return render_template(
        "edit_invoice.html", invoice=invoice, products=available_products
    )


@app.route("/invoices/add-item/<int:invoice_id>", methods=["POST"])
@login_required
def add_invoice_item(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if not invoice.can_edit:
        flash("Cannot modify a paid or cancelled invoice", "danger")
        return redirect(url_for("invoices"))

    product_id = safe_int_convert(request.form.get("product_id"))
    quantity = safe_int_convert(request.form.get("quantity"))

    if product_id <= 0 or quantity <= 0:
        flash("Invalid product or quantity.", "danger")
        return redirect(url_for("edit_invoice", invoice_id=invoice_id))

    product = Product.query.get_or_404(product_id)

    try:
        existing_item = InvoiceItem.query.filter_by(
            invoice_id=invoice_id, product_details=product_id
        ).first()
        if existing_item:
            new_qty = existing_item.quantity + quantity
            if new_qty > product.product_quantity + existing_item.quantity:
                flash(
                    f"Insufficient stock! Available: {product.product_quantity + existing_item.quantity}",
                    "danger",
                )
            else:
                existing_item.quantity = new_qty
                existing_item.calculate_total()
                product.product_quantity -= quantity
                record_stock_movement(
                    product_id, "sale", quantity, "invoice", invoice_id
                )
                invoice.calculate_totals()
                db.session.commit()
                flash("Item quantity updated!", "success")
        else:
            if quantity > product.product_quantity:
                flash(
                    f"Insufficient stock! Available: {product.product_quantity}",
                    "danger",
                )
            else:
                item = InvoiceItem(
                    invoice_id=invoice_id,
                    product_details=product_id,
                    quantity=quantity,
                    unit_price=product.product_price,
                )
                item.calculate_total()
                db.session.add(item)
                product.product_quantity -= quantity
                record_stock_movement(
                    product_id, "sale", quantity, "invoice", invoice_id
                )
                invoice.calculate_totals()
                db.session.commit()
                flash("Item added to invoice!", "success")
    except Exception as e:
        db.session.rollback()
        log_error("ADD_INVOICE_ITEM", str(e))
        flash(f"Error adding item: {str(e)}", "danger")

    return redirect(url_for("edit_invoice", invoice_id=invoice_id))


@app.route("/invoices/remove-item/<int:item_id>")
@login_required
def remove_invoice_item(item_id):
    item = InvoiceItem.query.get_or_404(item_id)
    invoice = db.session.get(Invoice, item.invoice_id)

    if not invoice.can_edit:
        flash("Cannot modify a paid or cancelled invoice", "danger")
        return redirect(url_for("invoices"))

    try:
        product = db.session.get(Product, item.product_details)
        product.product_quantity += item.quantity
        record_stock_movement(
            item.product_details,
            "return",
            item.quantity,
            "invoice",
            invoice.invoice_id,
            notes="Item removed from invoice",
        )

        invoice_id = item.invoice_id
        db.session.delete(item)
        invoice.calculate_totals()
        db.session.commit()
        flash("Item removed from invoice!", "success")
    except Exception as e:
        db.session.rollback()
        log_error("REMOVE_INVOICE_ITEM", str(e))
        flash(f"Error removing item: {str(e)}", "danger")
    return redirect(url_for("edit_invoice", invoice_id=invoice_id))


@app.route("/invoices/update-status/<int:invoice_id>", methods=["POST"])
@login_required
def update_invoice_status(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    new_status = request.form.get("status", "")

    if new_status not in ["paid", "pending", "cancelled"]:
        flash("Invalid status.", "danger")
        return redirect(url_for("invoices"))

    try:
        if new_status == "paid":
            invoice.status = "paid"
            invoice.payment_method = request.form.get("payment_method", "")[:50]
            invoice.payment_reference = request.form.get("payment_reference", "")[:255]
            invoice.payment_date = datetime.now()
            log_user_action("INVOICE_PAID", f"Invoice {invoice.invoice_number} marked as paid, method: {invoice.payment_method or 'N/A'}")
            flash(f"Invoice {invoice.invoice_number} marked as paid!", "success")
        elif new_status == "cancelled":
            if invoice.can_cancel:
                for item in invoice.items:
                    product = db.session.get(Product, item.product_details)
                    product.product_quantity += item.quantity
                    record_stock_movement(
                        item.product_details,
                        "return",
                        item.quantity,
                        "invoice",
                        invoice_id,
                        notes="Invoice cancelled",
                    )
                invoice.status = "cancelled"
                log_user_action("INVOICE_CANCELLED", f"Invoice {invoice.invoice_number} cancelled, stock returned")
                flash(
                    f"Invoice {invoice.invoice_number} cancelled and stock returned!",
                    "success",
                )
            else:
                flash("Cannot cancel this invoice", "danger")
                return redirect(url_for("invoices"))
        elif new_status == "pending":
            invoice.status = "pending"
            log_user_action("INVOICE_PENDING", f"Invoice {invoice.invoice_number} status changed to pending")
            flash(f"Invoice {invoice.invoice_number} marked as pending!", "success")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_error("UPDATE_INVOICE_STATUS", str(e))
        flash(f"Error updating invoice: {str(e)}", "danger")
    return redirect(url_for("invoices"))


@app.route("/invoices/delete/<int:invoice_id>")
@admin_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if not invoice.can_edit:
        flash("Cannot delete a paid or cancelled invoice", "danger")
        return redirect(url_for("invoices"))

    for item in invoice.items:
        product = db.session.get(Product, item.product_details)
        product.product_quantity += item.quantity
        record_stock_movement(
            item.product_details,
            "return",
            item.quantity,
            "invoice",
            invoice_id,
            notes="Invoice deleted",
        )

    invoice_number = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()
    log_user_action("INVOICE_DELETE", f"Deleted invoice: {invoice_number}, stock returned")
    flash(f"Invoice {invoice_number} deleted successfully!", "success")
    return redirect(url_for("invoices"))


@app.route("/invoice/print/<int:invoice_id>")
@login_required
def invoice_print(invoice_id):
    invoice = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product),
    ).get_or_404(invoice_id)
    return render_template("print_invoice.html", invoice=invoice)


@app.route("/reports/sales")
@login_required
def sales_report():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Invoice.query.options(
        joinedload(Invoice.customer),
        joinedload(Invoice.items).joinedload(InvoiceItem.product),
    ).filter(Invoice.status == "paid")

    if start_date:
        query = query.filter(db.func.date(Invoice.created_at) >= start_date)
    if end_date:
        query = query.filter(db.func.date(Invoice.created_at) <= end_date)

    invoices = query.order_by(Invoice.created_at.desc()).all()

    total_sales = sum(inv.total for inv in invoices)
    total_tax = sum(inv.tax_amount for inv in invoices)
    total_discount = sum(inv.discount_amount for inv in invoices)

    return render_template(
        "sales_report.html",
        invoices=invoices,
        total_sales=total_sales,
        total_tax=total_tax,
        total_discount=total_discount,
        start_date=start_date,
        end_date=end_date,
    )


@app.route("/reports/stock")
@login_required
def stock_report():
    products = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.product_quantity.asc())
        .all()
    )
    total_value = sum(p.product_price * p.product_quantity for p in products)
    low_stock_count = sum(1 for p in products if p.is_low_stock)
    out_of_stock_count = sum(1 for p in products if p.product_quantity == 0)

    return render_template(
        "stock_report.html",
        products=products,
        total_value=total_value,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
    )


@app.route("/export/products")
@login_required
def export_products():
    """Export products to CSV."""
    log_user_action("EXPORT", "Exported products to CSV")
    products = Product.query.filter_by(is_active=True).all()
    return export_products_csv(products)


@app.route("/export/customers")
@login_required
def export_customers():
    """Export customers to CSV."""
    log_user_action("EXPORT", "Exported customers to CSV")
    customers = Customer.query.filter_by(is_active=True).all()
    return export_customers_csv(customers)


@app.route("/export/invoices")
@login_required
def export_invoices():
    """Export invoices to CSV."""
    log_user_action("EXPORT", "Exported invoices to CSV")
    status_filter = request.args.get("status", "all")
    query = Invoice.query.options(joinedload(Invoice.customer))

    if status_filter != "all":
        query = query.filter(Invoice.status == status_filter)

    invoices = query.order_by(Invoice.created_at.desc()).all()
    return export_invoices_csv(invoices)


@app.route("/export/sales-report")
@login_required
def export_sales():
    """Export sales report to CSV."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    log_user_action(
        "EXPORT", f"Exported sales report to CSV ({start_date} to {end_date})"
    )

    query = Invoice.query.options(joinedload(Invoice.customer)).filter(
        Invoice.status == "paid"
    )

    if start_date:
        query = query.filter(db.func.date(Invoice.created_at) >= start_date)
    if end_date:
        query = query.filter(db.func.date(Invoice.created_at) <= end_date)

    invoices = query.order_by(Invoice.created_at.desc()).all()

    total_sales = sum(inv.total for inv in invoices)
    total_tax = sum(inv.tax_amount for inv in invoices)
    total_discount = sum(inv.discount_amount for inv in invoices)

    return export_sales_report_csv(invoices, total_sales, total_tax, total_discount)


@app.route("/search/products")
@login_required
def search_products_ajax():
    """AJAX search for products."""
    term = sanitize_search_input(request.args.get("q", ""))
    products = search_products(term).limit(10).all()
    return jsonify(
        [
            {
                "id": p.product_id,
                "name": p.product_name,
                "model": p.product_model,
                "price": float(p.product_price),
                "quantity": p.product_quantity,
            }
            for p in products
        ]
    )


@app.route("/search/customers")
@login_required
def search_customers_ajax():
    """AJAX search for customers."""
    term = sanitize_search_input(request.args.get("q", ""))
    customers = search_customers(term).limit(10).all()
    return jsonify(
        [
            {"id": c.customer_id, "name": c.full_name, "phone": c.phone_number}
            for c in customers
        ]
    )


@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), 500


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host=host, port=port, debug=Config.DEBUG)
