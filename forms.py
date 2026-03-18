from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange, Optional, Length

class CustomerForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=255)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=255)])
    phone_number = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    customer_address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=255)])
    submit = SubmitField('Save Customer')

class ProductForm(FlaskForm):
    product_type = StringField('Product Type', validators=[DataRequired(), Length(max=255)])
    product_name = StringField('Product Name', validators=[DataRequired(), Length(max=255)])
    product_model = StringField('Model', validators=[DataRequired(), Length(max=255)])
    product_color = StringField('Color', validators=[DataRequired(), Length(max=255)])
    product_price = FloatField('Price (LKR)', validators=[DataRequired(), NumberRange(min=0)])
    product_quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    low_stock_threshold = IntegerField('Low Stock Threshold', default=5, validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Product')
