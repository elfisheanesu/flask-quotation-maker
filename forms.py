from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, IntegerField, SelectField, TextAreaField, EmailField, DateField, FileField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError, NumberRange
from datetime import date
from models import Product

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class CustomerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Submit')

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')

class QuotationForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    submit = SubmitField('Create Quotation')

class QuotationItemForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Add Item')

class PurchaseOrderForm(FlaskForm):
    supplier = StringField('Supplier', validators=[DataRequired(), Length(max=100)])
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    submit = SubmitField('Save Purchase Order')

class PurchaseOrderItemForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Add Item')

    def __init__(self, *args, **kwargs):
        super(PurchaseOrderItemForm, self).__init__(*args, **kwargs)
        self.product_id.choices = [(p.id, p.name) for p in Product.query.all()]

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired()])
    street_address = StringField('Street Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    postal_code = StringField('Postal Code', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    logo = FileField('Company Logo', validators=[Optional()])
    submit = SubmitField('Save Changes')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise ValidationError('Passwords must match')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6)])
    is_admin = BooleanField('Is Administrator')
    submit = SubmitField('Add User')

    def validate_confirm_password(self, field):
        if field.data != self.password.data:
            raise ValidationError('Passwords must match')

class UserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional(), Length(min=6)])
    is_admin = BooleanField('Is Administrator')
    submit = SubmitField('Update User')

    def validate_confirm_password(self, field):
        if self.password.data and field.data != self.password.data:
            raise ValidationError('Passwords must match')
