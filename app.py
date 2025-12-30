import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.secret_key = "HeartScript_Secure_Vault_#2025" 
CORS(app)

# --- Database Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500), default="https://via.placeholder.com/300")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    
    # --- UPDATED: Detailed Address Fields ---
    house_no = db.Column(db.String(100), nullable=False) 
    address = db.Column(db.Text, nullable=False)        # Area/Colony
    landmark = db.Column(db.String(100), nullable=True)  
    pincode = db.Column(db.String(10), nullable=False)
    
    # --- UPDATED: Personalization Field ---
    custom_details = db.Column(db.Text, nullable=False) # User story/Instructions
    
    total = db.Column(db.String(20), nullable=False)
    items = db.Column(db.Text, nullable=False)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)

# --- User Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shop')
def shop():
    products = Product.query.all()
    return render_template('shop.html', products=products)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.json
        
        # Check: Naye fields ko validate kar rahe hain
        required_fields = ("name", "phone", "email", "house_no", "address", "pincode", "custom_details", "total", "items")
        if not all(k in data for k in required_fields):
            return jsonify({"status": "error", "message": "Missing required details for HeartScript experience"}), 400

        new_order = Order(
            name=data['name'],
            phone=data['phone'],
            email=data['email'],
            house_no=data['house_no'],
            address=data['address'],
            landmark=data.get('landmark', ''), # Optional
            pincode=data['pincode'],
            custom_details=data['custom_details'], # Personalization details
            total=data['total'],
            items=str(data['items'])
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"status": "success", "order_id": new_order.id})
    except Exception as e:
        db.session.rollback()
        print(f"CRITICAL ERROR: {e}")
        return jsonify({"status": "error", "message": f"Database Error: {str(e)}"}), 500

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
            session['admin_logged_in'] = True
            flash("Dashboard Accessed!", "success")
            return redirect(url_for('admin'))
        else:
            flash("Wrong Password!", "danger")
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    orders = Order.query.order_by(Order.date_ordered.desc()).all()
    products = Product.query.all()
    return render_template('admin.html', orders=orders, products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    name = request.form.get('name')
    price = request.form.get('price')
    image_url = request.form.get('image_url')
    new_product = Product(name=name, price=price, image_url=image_url)
    db.session.add(new_product)
    db.session.commit()
    flash("Product added successfully!", "success")
    return redirect(url_for('admin'))

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if not session.get('admin_logged_in'): return redirect(url_for('login'))
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted!", "info")
    return redirect(url_for('admin'))

# --- NEW FEATURE: Delete Order ---
@app.route('/delete_order/<int:id>')
def delete_order(id):
    if not session.get('admin_logged_in'): 
        return redirect(url_for('login'))
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash(f"Order #{id} has been permanently removed.", "info")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(host='0.0.0.0', port=5000, debug=True)
