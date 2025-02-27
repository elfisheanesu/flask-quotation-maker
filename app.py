from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, CustomerForm, ProductForm, QuotationForm, QuotationItemForm, PurchaseOrderForm, PurchaseOrderItemForm, CompanyForm, RegistrationForm, UserForm, UserEditForm
from utils import generate_pdf_quotation, generate_pdf_invoice
from flask import send_file
from io import BytesIO
from uuid import uuid4
from werkzeug.utils import secure_filename
from extensions import db, migrate, login_manager
from models import User, Company, Customer, Product, Quotation, QuotationItem, Invoice, PurchaseOrder, PurchaseOrderItem
from flask_login import login_user, login_required, logout_user, current_user
import pdfkit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quotation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new company for the user
        company = Company(
            name='Your Company Name',
            street_address='123 Business Street',
            city='Business City',
            postal_code='12345',
            email=form.email.data,  # Use registering user's email as default
            phone='(123) 456-7890'
        )
        db.session.add(company)
        db.session.commit()
        
        # Create user
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            is_admin=True,  # First user of company is admin
            company=company
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/users')
@login_required
def list_users():
    if not current_user.is_admin:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.filter_by(company_id=current_user.company_id).all()
    return render_template('users/list.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('You do not have permission to add users.', 'danger')
        return redirect(url_for('index'))
    
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'danger')
            return render_template('users/form.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'danger')
            return render_template('users/form.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            is_admin=form.is_admin.data,
            company_id=current_user.company_id
        )
        db.session.add(user)
        db.session.commit()
        
        flash('User added successfully!', 'success')
        return redirect(url_for('list_users'))
    
    return render_template('users/form.html', form=form)

@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not current_user.is_admin:
        flash('You do not have permission to edit users.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    if user.company_id != current_user.company_id:
        flash('You do not have permission to edit this user.', 'danger')
        return redirect(url_for('list_users'))
    
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        
        if form.password.data:
            user.password = generate_password_hash(form.password.data)
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('list_users'))
    
    return render_template('users/form.html', form=form, user=user)

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    if user.company_id != current_user.company_id:
        flash('You do not have permission to delete this user.', 'danger')
        return redirect(url_for('list_users'))
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('list_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('list_users'))

@app.route('/customers')
@login_required
def list_customers():
    customers = Customer.query.filter_by(company_id=current_user.company_id).all()
    return render_template('customers/list.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            company_id=current_user.company_id
        )
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('list_customers'))
    return render_template('customers/form.html', form=form)

@app.route('/customers/<int:id>')
@login_required
def view_customer(id):
    customer = Customer.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    return render_template('customers/view.html', customer=customer)

@app.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.name = form.name.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        customer.address = form.address.data
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('list_customers'))
    return render_template('customers/form.html', form=form, customer=customer)

@app.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def delete_customer(id):
    customer = Customer.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('list_customers'))

@app.route('/products')
@login_required
def list_products():
    products = Product.query.filter_by(company_id=current_user.company_id).all()
    return render_template('products/list.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            unit_price=form.unit_price.data,
            company_id=current_user.company_id
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('list_products'))
    return render_template('products/form.html', form=form)

@app.route('/products/<int:id>')
@login_required
def view_product(id):
    product = Product.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    return render_template('products/view.html', product=product)

@app.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.unit_price = form.unit_price.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('list_products'))
    return render_template('products/form.html', form=form, product=product)

@app.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('list_products'))

@app.route('/quotations')
@login_required
def list_quotations():
    quotations = Quotation.query.order_by(Quotation.date.desc()).all()
    return render_template('quotations/list.html', quotations=quotations)

@app.route('/purchases')
@login_required
def list_purchases():
    purchases = PurchaseOrder.query.order_by(PurchaseOrder.date.desc()).all()
    return render_template('purchases/list.html', purchases=purchases)

@app.route('/quotations/create', methods=['GET', 'POST'])
@login_required
def create_quotation():
    form = QuotationForm()
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.filter_by(company_id=current_user.company_id).order_by('name')]
    
    if form.validate_on_submit():
        quotation = Quotation(
            customer_id=form.customer_id.data,
            date=form.date.data,
            status='pending',
            total=0.0,
            company_id=current_user.company_id
        )
        db.session.add(quotation)
        db.session.commit()
        flash('Quotation created successfully', 'success')
        return redirect(url_for('edit_quotation', id=quotation.id))
    
    return render_template('quotations/form.html', form=form, title='Create Quotation')

@app.route('/purchases/create', methods=['GET', 'POST'])
@login_required
def create_purchase():
    form = PurchaseOrderForm()
    if form.validate_on_submit():
        purchase = PurchaseOrder(
    supplier_name=form.supplier.data,  
    date=form.date.data,
    company_id=current_user.company_id 
)
        db.session.add(purchase)
        db.session.commit()
        flash('Purchase order created successfully!', 'success')
        return redirect(url_for('edit_purchase', id=purchase.id))
    return render_template('purchases/form.html', form=form, title='Create Purchase Order')

@app.route('/quotations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quotation(id):
    quotation = Quotation.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    if quotation.status != 'pending':
        flash('Cannot edit approved quotation', 'danger')
        return redirect(url_for('view_quotation', id=id))
    
    form = QuotationForm(obj=quotation)
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.filter_by(company_id=current_user.company_id).order_by('name')]
    
    item_form = QuotationItemForm()
    item_form.product_id.choices = [(p.id, f"{p.name} (${p.unit_price:.2f})") for p in Product.query.filter_by(company_id=current_user.company_id).order_by('name')]
    
    if form.validate_on_submit():
        quotation.customer_id = form.customer_id.data
        quotation.date = form.date.data
        db.session.commit()
        flash('Quotation updated successfully', 'success')
        return redirect(url_for('edit_quotation', id=id))
    
    return render_template('quotations/form.html', 
                         form=form, 
                         item_form=item_form,
                         quotation=quotation,
                         title='Edit Quotation')

@app.route('/purchases/<int:id>')
@login_required
def view_purchase(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    return render_template('purchases/view.html', purchase=purchase)

@app.route('/purchases/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_purchase(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    if purchase.status != 'pending':
        flash('Cannot edit a received purchase order.', 'error')
        return redirect(url_for('view_purchase', id=id))
    
    form = PurchaseOrderForm(obj=purchase)
    item_form = PurchaseOrderItemForm()
    
    if form.validate_on_submit():
        purchase.supplier = form.supplier.data
        purchase.date = form.date.data
        db.session.commit()
        flash('Purchase order updated successfully!', 'success')
        return redirect(url_for('view_purchase', id=id))
    
    return render_template('purchases/form.html', 
                         form=form, 
                         item_form=item_form,
                         purchase=purchase,
                         title='Edit Purchase Order')

@app.route('/quotations/<int:id>/items/add', methods=['POST'])
@login_required
def add_quotation_item(id):
    quotation = Quotation.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    if quotation.status != 'pending':
        flash('Cannot modify approved quotation', 'danger')
        return redirect(url_for('view_quotation', id=id))
    
    form = QuotationItemForm()
    form.product_id.choices = [(p.id, p.name) for p in Product.query.filter_by(company_id=current_user.company_id).order_by('name')]
    
    if form.validate_on_submit():
        product = Product.query.filter_by(id=form.product_id.data, company_id=current_user.company_id).first()
        if product:
            item = QuotationItem(
                quotation_id=quotation.id,
                product_id=form.product_id.data,
                quantity=form.quantity.data,
                unit_price=product.unit_price,
                total=product.unit_price * form.quantity.data
            )
            db.session.add(item)
            quotation.total = sum(item.total for item in quotation.items) + item.total
            db.session.commit()
            flash('Item added successfully', 'success')
        else:
            flash('Invalid product selected', 'danger')
    return redirect(url_for('edit_quotation', id=id))

@app.route('/purchases/<int:id>/items/add', methods=['POST'])
@login_required
def add_purchase_item(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    if purchase.status != 'pending':
        flash('Cannot add items to a received purchase order.', 'error')
        return redirect(url_for('view_purchase', id=id))
    
    form = PurchaseOrderItemForm()
    if form.validate_on_submit():
        total_price = form.quantity.data * form.unit_price.data  # Calculate total

        item = PurchaseOrderItem(
            purchase_order=purchase,
            product_id=form.product_id.data,
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            total=total_price  # Assign total value
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully!', 'success')

    return redirect(url_for('edit_purchase', id=id))


@app.route('/quotations/<int:quotation_id>/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_quotation_item(quotation_id, item_id):
    quotation = Quotation.query.filter_by(id=quotation_id, company_id=current_user.company_id).first_or_404()
    if quotation.status != 'pending':
        flash('Cannot modify approved quotation', 'danger')
        return redirect(url_for('view_quotation', id=quotation_id))
    
    item = QuotationItem.query.get_or_404(item_id)
    if item.quotation_id != quotation_id:
        flash('Invalid item', 'danger')
        return redirect(url_for('view_quotation', id=quotation_id))
    
    quotation.total -= item.total
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully', 'success')
    return redirect(url_for('edit_quotation', id=quotation_id))

@app.route('/purchases/<int:purchase_id>/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_purchase_item(purchase_id, item_id):
    purchase = PurchaseOrder.query.get_or_404(purchase_id)
    if purchase.status != 'pending':
        flash('Cannot delete items from a received purchase order.', 'error')
        return redirect(url_for('view_purchase', id=purchase_id))
    
    item = PurchaseOrderItem.query.get_or_404(item_id)
    if item.purchase_order_id != purchase_id:
        abort(404)
    
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('edit_purchase', id=purchase_id))

@app.route('/quotations/<int:id>')
@login_required
def view_quotation(id):
    quotation = Quotation.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    return render_template('quotations/view.html', quotation=quotation)

@app.route('/quotations/<int:id>/download')
@login_required
# def download_quotation(id):
#     quotation = Quotation.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    
#     # Create a PDF using a template
#     html = render_template('quotations/pdf.html', quotation=quotation)
    
#     # Convert HTML to PDF
#     pdf = pdfkit.from_string(html, False)
    
#     # Create response
#     response = make_response(pdf)
#     response.headers['Content-Type'] = 'application/pdf'
#     response.headers['Content-Disposition'] = f'attachment; filename=quotation_{quotation.id}.pdf'
    
#     return response
def download_quotation(id):
    try:
        quotation = Quotation.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()

        # Create a PDF using a template
        html = render_template('quotations/pdf.html', quotation=quotation)

        # Provide the correct path to wkhtmltopdf
        config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

        # Convert HTML to PDF
        pdf = pdfkit.from_string(html, False, configuration=config)

        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=quotation_{quotation.id}.pdf'

        return response

    except FileNotFoundError:
        return "Error: wkhtmltopdf executable not found. Please check the installation path.", 500
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route('/quotations/<int:id>/approve', methods=['POST'])
@login_required
def approve_quotation(id):
    quotation = Quotation.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    if quotation.status == 'pending':
        quotation.status = 'approved'
        db.session.commit()
        flash('Quotation approved successfully', 'success')
    else:
        flash('Quotation already approved', 'warning')
    return redirect(url_for('view_quotation', id=id))

@app.route('/quotations/<int:id>/delete', methods=['POST'])
@login_required
def delete_quotation(id):
    quotation = Quotation.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    if quotation.status != 'pending':
        flash('Cannot delete approved quotation', 'danger')
        return redirect(url_for('view_quotation', id=id))
    
    db.session.delete(quotation)
    db.session.commit()
    flash('Quotation deleted successfully', 'success')
    return redirect(url_for('list_quotations'))

@app.route('/quotations/<int:quotation_id>/create-invoice', methods=['GET', 'POST'])
@login_required
# def create_invoice(quotation_id):
#     quotation = Quotation.query.get_or_404(quotation_id)
#     if quotation.status != 'approved':
#         flash('Can only create invoice for approved quotation', 'danger')
#         return redirect(url_for('view_quotation', id=quotation_id))
    
#     if quotation.invoice:
#         flash('Invoice already exists', 'warning')
#         return redirect(url_for('view_invoice', id=quotation.invoice.id))
    
#     invoice = Invoice(
#         quotation_id=quotation.id,
#         date=datetime.now(),
#         due_date=datetime.now() + timedelta(days=30),
#         status='unpaid'
#     )
#     db.session.add(invoice)
#     db.session.commit()
    
#     flash('Invoice created successfully', 'success')
#     return redirect(url_for('view_invoice', id=invoice.id))
def create_invoice(quotation_id):
    quotation = Quotation.query.get_or_404(quotation_id)
    if quotation.status != 'approved':
        flash('Can only create invoice for approved quotation', 'danger')
        return redirect(url_for('view_quotation', id=quotation_id))
    
    if quotation.invoice:
        flash('Invoice already exists', 'warning')
        return redirect(url_for('view_invoice', id=quotation.invoice.id))
    
    # Get the company_id from the associated customer
    company_id = quotation.customer.company_id
    
    invoice = Invoice(
        quotation_id=quotation.id,
        date=datetime.now(),
        due_date=datetime.now() + timedelta(days=30),
        status='unpaid',
        company_id=company_id  # Set the company_id here
    )
    db.session.add(invoice)
    db.session.commit()
    
    flash('Invoice created successfully', 'success')
    return redirect(url_for('view_invoice', id=invoice.id))


@app.route('/purchases/<int:id>/receive', methods=['POST'])
@login_required
def receive_purchase(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    if purchase.status != 'pending':
        flash('Purchase order has already been received.', 'error')
        return redirect(url_for('view_purchase', id=id))
    
    if not purchase.items:
        flash('Cannot receive an empty purchase order.', 'error')
        return redirect(url_for('edit_purchase', id=id))
    
    # Update product stock levels
    for item in purchase.items:
        item.product.stock += item.quantity
    
    purchase.status = 'received'
    purchase.received_at = datetime.utcnow()
    db.session.commit()
    flash('Purchase order marked as received!', 'success')
    return redirect(url_for('view_purchase', id=id))

@app.route('/purchases/<int:id>/delete', methods=['POST'])
@login_required
def delete_purchase(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    if purchase.status != 'pending':
        flash('Cannot delete a received purchase order.', 'error')
        return redirect(url_for('view_purchase', id=id))
    
    db.session.delete(purchase)
    db.session.commit()
    flash('Purchase order deleted successfully!', 'success')
    return redirect(url_for('list_purchases'))

@app.route('/invoices')
@login_required
def list_invoices():
    invoices = Invoice.query.order_by(Invoice.date.desc()).all()
    return render_template('invoices/list.html', invoices=invoices)

@app.route('/invoices/<int:id>')
@login_required
def view_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/view.html', invoice=invoice)

@app.route('/invoices/<int:id>/download')
@login_required
def download_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    pdf = generate_pdf_invoice(invoice)
    return send_file(
        BytesIO(pdf),
        download_name=f'invoice_{invoice.id}.pdf',
        mimetype='application/pdf'
    )

@app.route('/invoices/<int:id>/mark-paid', methods=['POST'])
@login_required
def mark_invoice_paid(id):
    invoice = Invoice.query.get_or_404(id)
    invoice.status = 'paid'
    db.session.commit()
    flash('Invoice marked as paid', 'success')
    return redirect(url_for('view_invoice', id=id))

@app.route('/company/settings', methods=['GET', 'POST'])
@login_required
def company_settings():
    company = Company.get_or_create()
    form = CompanyForm(obj=company)
    
    if form.validate_on_submit():
        form.populate_obj(company)
        
        # Handle logo upload
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and allowed_file(logo.filename):
                # Secure the filename
                filename = secure_filename(logo.filename)
                # Generate unique filename
                unique_filename = f"{uuid4()}_{filename}"
                # Save the file
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                # Update company logo filename
                company.logo_filename = unique_filename

        db.session.commit()
        flash('Company settings updated successfully!', 'success')
        return redirect(url_for('company_settings'))
    
    return render_template('company/settings.html', form=form, company=company)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
