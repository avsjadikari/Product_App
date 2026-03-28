from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    FloatField,
    IntegerField,
    SubmitField,
    PasswordField,
    BooleanField,
    DecimalField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    NumberRange,
    Optional,
    Length,
    Regexp,
)


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")


class CustomerForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=255)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=255)])
    phone_number = StringField("Phone", validators=[DataRequired(), Length(max=20)])
    customer_address = StringField(
        "Address", validators=[DataRequired(), Length(max=255)]
    )
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    submit = SubmitField("Save Customer")


class ProductForm(FlaskForm):
    product_type = StringField(
        "Product Type", validators=[DataRequired(), Length(max=255)]
    )
    product_name = StringField(
        "Product Name", validators=[DataRequired(), Length(max=255)]
    )
    product_model = StringField("Model", validators=[DataRequired(), Length(max=255)])
    product_color = StringField("Color", validators=[DataRequired(), Length(max=255)])
    product_price = FloatField(
        "Price (LKR)", validators=[DataRequired(), NumberRange(min=0)]
    )
    product_quantity = IntegerField(
        "Quantity", validators=[DataRequired(), NumberRange(min=0)]
    )
    low_stock_threshold = IntegerField(
        "Low Stock Threshold", default=5, validators=[Optional(), NumberRange(min=0)]
    )
    submit = SubmitField("Save Product")


class UserForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    role = StringField("Role", validators=[DataRequired()])
    submit = SubmitField("Create User")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=8)]
    )
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Change Password")


class InvoiceForm(FlaskForm):
    customer_id = IntegerField("Customer", validators=[DataRequired()])
    tax_rate = FloatField(
        "Tax Rate (%)", validators=[Optional(), NumberRange(min=0, max=100)]
    )
    discount_amount = FloatField(
        "Discount Amount", validators=[Optional(), NumberRange(min=0)]
    )
    notes = StringField("Notes", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Create Invoice")


class InvoiceItemForm(FlaskForm):
    product_id = IntegerField("Product", validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Add Item")


class StockAdjustForm(FlaskForm):
    product_id = IntegerField("Product", validators=[DataRequired()])
    quantity = IntegerField("Quantity Adjustment", validators=[DataRequired()])
    notes = StringField("Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Adjust Stock")


class CheckoutForm(FlaskForm):
    customer_id = IntegerField("Customer", validators=[DataRequired()])
    tax_rate = FloatField(
        "Tax Rate (%)", validators=[Optional(), NumberRange(min=0, max=100)]
    )
    discount_amount = FloatField(
        "Discount Amount", validators=[Optional(), NumberRange(min=0)]
    )
    submit = SubmitField("Checkout")


class CartUpdateForm(FlaskForm):
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Update")


class InvoiceStatusForm(FlaskForm):
    status = StringField("Status", validators=[DataRequired()])
    payment_method = StringField(
        "Payment Method", validators=[Optional(), Length(max=50)]
    )
    payment_reference = StringField(
        "Payment Reference", validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Update Status")


class CartAddForm(FlaskForm):
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Add to Cart")


class SetupForm(FlaskForm):
    db_host = StringField("Database Host", validators=[DataRequired(), Length(max=255)])
    db_port = StringField("Database Port", validators=[DataRequired(), Length(max=10)])
    db_name = StringField("Database Name", validators=[DataRequired(), Length(max=255)])
    db_user = StringField(
        "Database Username", validators=[DataRequired(), Length(max=255)]
    )
    db_password = PasswordField("Database Password")
    secret_key = StringField(
        "Application Secret Key", validators=[DataRequired(), Length(min=32, max=255)]
    )
    submit = SubmitField("Save Configuration")
