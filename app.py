import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)

# --- Security & Session Fix for Render ---
app.secret_key = os.environ.get('SECRET_KEY', 'HeartScript_Secure_Vault_#2025')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=1)
)

CORS(app)

# --- Database Configuration (Render Stable Path) ---
basedir = os.path.abspath(os.path.dirname(__file__))
# Ye line ensure karti hai ki Render par file permissions ka error na aaye
sqlite_path = 'sqlite:///' + os.path.join(basedir, 'database.db')

db_uri = os.environ.get('DATABASE_URL', sqlite_path)
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models (No Content Deleted) ---

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    products = db.relationship('Product', backref='category_ref', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500), default="https://via.placeholder.com/300")
    description = db.Column(db.Text, nullable=True) 
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    house_no = db.Column(db.String(100), nullable=False) 
    address = db.Column(db.Text, nullable=False)
    landmark = db.Column(db.String(100), nullable=True)  
    pincode = db.Column(db.String(10), nullable=False)
    custom_details = db.Column(db.Text, nullable=False) 
    total = db.Column(db.String(20), nullable=False)
    items = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Pending") 
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)

# --- User Routes ---

@app.route('/')
def home():
    featured_products = Product.query.limit(4).all()
    return render_template('index.html', featured=featured_products)

@app.route('/shop')
def shop():
    categories = Category.query.all()
    selected_cat_id = request.args.get('category')
    if selected_cat_id and selected_cat_id != 'None':
        products = Product.query.filter_by(category_id=selected_cat_id).all()
    else:
        products = Product.query.all()
    return render_template('shop.html', products=products, categories=categories, selected_cat=selected_cat_id)

@app.route('/product/<int:product_id>')
def product_view(product_id):
    product = Product.query.get_or_404(product_id)
    related = Product.query.filter(Product.category_id == product.category_id, Product.id != product_id).limit(3).all()
    return render_template('product_view.html', product=product, related=related)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.json
        items_str = str(data['items']) if isinstance(data['items'], (list, dict)) else data['items']
        new_order = Order(
            name=data['name'], phone=data['phone'], email=data['email'],
            house_no=data['house_no'], address=data['address'], landmark=data.get('landmark', ''),
            pincode=data['pincode'], custom_details=data['custom_details'],
            total=data['total'], items=items_str
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"status": "success", "order_id": new_order.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/thank-you/<int:order_id>')
def thank_you(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('thank_you.html', order=order)

# --- Admin Section ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'HeartScript@Admin2025': 
            session.permanent = True
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        flash("Wrong Password!", "danger")
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    try:
        orders = Order.query.order_by(Order.date_ordered.desc()).all()
        products = Product.query.all()
        categories = Category.query.all()
        return render_template('admin.html', orders=orders, products=products, categories=categories)
    except Exception as e:
        return f"Database Error: {str(e)}"

@app.route('/add_category', methods=['POST'])
def add_category():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    cat_name = request.form.get('name')
    if cat_name:
        new_cat = Category(name=cat_name)
        db.session.add(new_cat)
        db.session.commit()
        flash("New Collection Category Added!", "success")
    return redirect(url_for('admin'))

@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    try:
        new_product = Product(
            name=request.form.get('name'),
            price=int(request.form.get('price')),
            image_url=request.form.get('image_url'),
            description=request.form.get('description'), 
            category_id=int(request.form.get('category_id'))
        )
        db.session.add(new_product)
        db.session.commit()
        flash(f"'{new_product.name}' added to your gallery!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('admin'))

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash("Product removed.", "info")
    return redirect(url_for('admin'))

@app.route('/delete_order/<int:id>')
def delete_order(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash("Order record deleted.", "info")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- Startup ---

# --- Startup Logic (Temporary Reset) ---
with app.app_context():
    # Pehle purani table delete hogi phir nayi banegi (Email column ke saath)
    # Note: Isse aapke purane dummy orders delete ho jayenge
    db.drop_all() 
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
