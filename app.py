import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from fpdf import FPDF
import io
import tempfile

app = Flask(__name__)

# --- 1. Security & Session Configuration ---
app.secret_key = os.environ.get('SECRET_KEY', 'HeartScript_Secure_Vault_#2026')
app.config.update(
    SESSION_COOKIE_SECURE=False, 
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)

CORS(app)

# --- 2. Cloudinary Configuration ---
cloudinary.config( 
  cloud_name = "dgmbcrasj", 
  api_key = "726246999652237", 
  api_secret = "ViB-jyArVkUUxkBiDZzJiypguyk", 
  secure = True
)

# --- 3. Local Database Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'heartscript_v2.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 4. Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    role = db.Column(db.String(20), default='customer')
    
    ans1 = db.Column(db.String(100), nullable=True)
    ans2 = db.Column(db.String(100), nullable=True)
    ans3 = db.Column(db.String(100), nullable=True)
    ans4 = db.Column(db.String(100), nullable=True)
    ans5 = db.Column(db.String(100), nullable=True)
    ans6 = db.Column(db.String(100), nullable=True)
    ans7 = db.Column(db.String(100), nullable=True)
    
    profile_pic = db.Column(db.String(500), default="https://res.cloudinary.com/dgmbcrasj/image/upload/v1710000000/default_avatar.png")
    orders = db.relationship('Order', backref='customer', lazy=True)

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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    house_no = db.Column(db.String(100), nullable=True) 
    address = db.Column(db.Text, nullable=False)
    landmark = db.Column(db.String(100), nullable=True)  
    pincode = db.Column(db.String(10), nullable=True)
    custom_details = db.Column(db.Text, nullable=True)
    total = db.Column(db.String(20), nullable=False)
    items = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Pending") 
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)

# --- 5. Auth Decorators & Routes ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to proceed.", "info")
            return redirect(url_for('user_login'))
        
        # Stability Fix: Ensure user still exists in DB
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            flash("Account error. Please login again.", "danger")
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(request.form.get('password'))
        
        ans_data = {
            'ans1': request.form.get('ans1', '').strip().lower(),
            'ans2': request.form.get('ans2', '').strip().lower(),
            'ans3': request.form.get('ans3', '').strip().lower(),
            'ans4': request.form.get('ans4', '').strip().lower(),
            'ans5': request.form.get('ans5', '').strip().lower(),
            'ans6': request.form.get('ans6', '').strip().lower(),
            'ans7': request.form.get('ans7', '').strip().lower()
        }

        filled_answers = [v for v in ans_data.values() if v != '']
        if len(filled_answers) < 3:
            flash("Please answer at least 3 security questions!", "warning")
            return redirect(url_for('register'))

        new_user = User(
            username=request.form.get('username'),
            email=email,
            password_hash=hashed_pw,
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            pincode=request.form.get('pincode'),
            **ans_data 
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created! Welcome to HeartScript.", "success")
        return redirect(url_for('user_login'))
    return render_template('register.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            session.permanent = True
            session['user_id'] = user.id
            session['user_name'] = user.username
            session['user_email'] = user.email
            session['user_profile_pic'] = user.profile_pic
            return redirect(url_for('home'))
        flash("Invalid email or password.", "danger")
    return render_template('user_login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with this email.", "danger")
            return redirect(url_for('forgot_password'))
        
        provided_answers = [
            request.form.get('ans1', '').strip().lower(),
            request.form.get('ans2', '').strip().lower(),
            request.form.get('ans3', '').strip().lower(),
            request.form.get('ans4', '').strip().lower(),
            request.form.get('ans5', '').strip().lower(),
            request.form.get('ans6', '').strip().lower(),
            request.form.get('ans7', '').strip().lower()
        ]
        db_answers = [user.ans1, user.ans2, user.ans3, user.ans4, user.ans5, user.ans6, user.ans7]
        
        matches = 0
        for i in range(7):
            if provided_answers[i] and db_answers[i] and provided_answers[i] == db_answers[i]:
                matches += 1
        
        if matches >= 3:
            new_password = request.form.get('new_password')
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Success! Password updated. You can login now.", "success")
            return redirect(url_for('user_login'))
        else:
            flash(f"Verification Failed! Only {matches} answers matched.", "danger")
    return render_template('forgot_password.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')
        user.pincode = request.form.get('pincode')
        
        file_to_upload = request.files.get('profile_pic')
        if file_to_upload and file_to_upload.filename != '':
            try:
                upload_result = cloudinary.uploader.upload(
                    file_to_upload,
                    folder="heartscript_profiles/",
                    transformation=[{'width': 400, 'height': 400, 'crop': "fill", 'gravity': "face"}]
                )
                user.profile_pic = upload_result['secure_url']
                session['user_profile_pic'] = user.profile_pic
            except Exception as e:
                flash(f"Upload error: {str(e)}", "danger")

        db.session.commit()
        flash("Profile updated successfully! ❤️", "success")
        return redirect(url_for('profile'))

    orders = Order.query.filter_by(user_id=user.id).order_by(Order.date_ordered.desc()).all()
    return render_template('profile.html', user=user, orders=orders)

# --- 6. Store Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shop')
def shop():
    categories = Category.query.all()
    selected_cat = request.args.get('category')
    if selected_cat and selected_cat != 'None':
        products = Product.query.filter_by(category_id=selected_cat).all()
    else:
        products = Product.query.all()
    return render_template('shop.html', products=products, categories=categories, selected_cat=selected_cat)

@app.route('/product/<int:product_id>')
def product_view(product_id):
    product = Product.query.get_or_404(product_id)
    related = Product.query.filter(Product.category_id == product.category_id, Product.id != product_id).limit(3).all()
    return render_template('product_view.html', product=product, related=related)

# --- 7. Order Submission ---
@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.get_json()
        new_order = Order(
            user_id=session.get('user_id'), 
            name=data.get('name', 'N/A'), 
            phone=str(data.get('phone', 'N/A')), 
            email=data.get('email'),
            house_no=data.get('house_no', 'N/A'), 
            address=data.get('address', 'N/A'), 
            landmark=data.get('landmark', ''),
            pincode=data.get('pincode'), 
            custom_details=data.get('custom_details'),
            total=str(data.get('total', '0')), 
            items=str(data.get('items', 'Unknown Item'))
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"success": True, "order_id": new_order.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/thank_you/<int:order_id>')
def thank_you(order_id):
    order_data = Order.query.get_or_404(order_id)
    return render_template('thank_you.html', order=order_data)

# --- 8. ROMANTIC INVOICE ---
# --- 8. PREMIUM ROMANTIC INVOICE (FIXED UNICODE ERROR) ---
@app.route('/download_invoice/<int:order_id>')
def download_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    pdf = FPDF()
    pdf.add_page()
    
    # --- Background & Border ---
    pdf.set_draw_color(255, 182, 193) 
    pdf.rect(5, 5, 200, 287)
    
    # --- Header: Brand Name ---
    pdf.set_font("helvetica", "B", 35)
    pdf.set_text_color(255, 65, 108)
    pdf.cell(0, 25, "HeartScript", 0, 1, 'C')
    
    pdf.set_font("helvetica", "I", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, -10, "Where every script tells a story...", 0, 1, 'C')
    pdf.ln(20)
    
    # --- Brand Description ---
    pdf.set_fill_color(255, 245, 247)
    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(80, 80, 80)
    description = (
        "HeartScript is more than just a gifting studio; it is a sanctuary for emotions in this digital age. "
        "We believe that while messages can be typed, souls can only be scripted. Our artisans carefully "
        "hand-carve your most cherished memories into timeless legacies using the art of traditional calligraphy. "
        "Every stroke of our pen is fueled by the love you hold for your dear ones. From vintage letters to "
        "personalized masterpieces, we ensure that your feelings aren't just delivered, but preserved forever. "
        "Thank you for choosing HeartScript to be a small part of your beautiful story. We script, you feel."
    )
    pdf.multi_cell(0, 5, description, 0, 'C', True)
    pdf.ln(10)
    
    # --- Order Info ---
    pdf.set_draw_color(200, 200, 200)
    pdf.line(15, 95, 195, 95)
    
    pdf.set_y(100)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(100, 8, f"Customer: {order.name}", 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f"Date: {order.date_ordered.strftime('%d-%m-%Y')}", 0, 1, 'R')
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(100, 6, f"Order ID: #HS-{order.id}", 0, 0)
    pdf.cell(0, 6, f"Status: {order.status}", 0, 1, 'R')
    pdf.ln(5)
    
    # --- Address & Personalization ---
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, "Shipping Details:", 0, 1)
    pdf.set_font("helvetica", "", 9)
    address_text = f"House No: {order.house_no}, {order.address}\nLandmark: {order.landmark}\nPIN: {order.pincode} | Phone: {order.phone}"
    pdf.multi_cell(0, 5, address_text)
    
    if order.custom_details:
        pdf.ln(3)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(255, 65, 108)
        # Yahan se emoji hata diya gaya hai taaki crash na ho
        pdf.multi_cell(0, 5, f"Customization: {order.custom_details}")
    pdf.ln(8)

    # --- Items Table ---
    pdf.set_fill_color(255, 65, 108)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(140, 10, " Description of Masterpiece", 1, 0, 'L', True)
    pdf.cell(40, 10, "Amount (INR)", 1, 1, 'C', True)
    
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(140, 12, f" {order.items}", 1)
    pdf.cell(40, 12, f"Rs. {order.total}", 1, 1, 'C')
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(255, 65, 108)
    pdf.cell(0, 10, f"Grand Total: Rs. {order.total}", 0, 1, 'R')
    
    # --- Footer Contact ---
    pdf.set_y(-55)
    pdf.set_draw_color(255, 182, 193)
    pdf.line(30, 245, 180, 245)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Connect With Our Studio", 0, 1, 'C')
    
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 5, "WhatsApp: +91 6394174932 | Instagram: @heartscript025.in", 0, 1, 'C')
    pdf.cell(0, 5, "Email: heartscript025@gmail.com | Web: www.heartscript.com", 0, 1, 'C')
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(255, 65, 108)
    # Emoji ki jagah humne text rakha hai
    pdf.cell(0, 10, "Thank you for letting us script your emotions.", 0, 1, 'C')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        return send_file(tmp.name, as_attachment=True, download_name=f"HeartScript_Invoice_{order.id}.pdf")

# --- 9. Admin Routes ---
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login(): 
    if request.method == 'POST':
        if request.form.get('password') == 'HeartScript@Admin2025':
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        flash("Wrong Password!", "danger")
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    orders = Order.query.order_by(Order.date_ordered.desc()).all()
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin.html', orders=orders, products=products, categories=categories)

@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    if not session.get('admin_logged_in'): return jsonify({"success": False}), 403
    order = Order.query.get(order_id)
    new_status = request.form.get('status')
    if order and new_status:
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order_id} status updated to {new_status}", "success")
    return redirect(url_for('admin'))

@app.route('/add_category', methods=['POST'])
def add_category():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    name = request.form.get('name')
    if name and not Category.query.filter_by(name=name).first():
        db.session.add(Category(name=name)); db.session.commit()
        flash("Category Added!", "success")
    return redirect(url_for('admin'))

@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    try:
        img_file = request.files.get('product_image')
        img_url = cloudinary.uploader.upload(img_file)['secure_url'] if img_file else "https://via.placeholder.com/300"
        new_prod = Product(
            name=request.form.get('name'), price=int(request.form.get('price')),
            image_url=img_url, description=request.form.get('description'), 
            category_id=int(request.form.get('category_id'))
        )
        db.session.add(new_prod); db.session.commit()
        flash("Product Added!", "success")
    except Exception as e: flash(str(e), "danger")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
