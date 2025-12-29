import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(current_dir, 'templates'))

# SQL Database Configuration (FIXED URI)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(current_dir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model (Table Structure)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    total = db.Column(db.String(20), nullable=False)
    items = db.Column(db.Text, nullable=False)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)

# Database Table Create karein (Only first time)
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

# Order Receive aur SQL mein save karne ka route
@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.json
        new_order = Order(
            name=data['name'],
            phone=data['phone'],
            address=data['address'],
            total=data['total'],
            items=str(data['items'])
        )
        db.session.add(new_order)
        db.session.commit()
        
        print(f"\n✅ SQL DATABASE UPDATED!")
        print(f"Order ID: {new_order.id} | Customer: {new_order.name}")
        
        return jsonify({"status": "success", "id": new_order.id})
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        return jsonify({"status": "error"}), 500

# ADMIN PANEL: Database se orders fetch karke dikhana
@app.route('/admin')
def admin():
    # Saare orders download date ke hisab se (latest first)
    all_orders = Order.query.order_by(Order.date_ordered.desc()).all()
    return render_template('admin.html', orders=all_orders)

# Naya Route: Order Delete karne ke liye
@app.route('/delete_order/<int:id>')
def delete_order(id):
    try:
        order_to_delete = Order.query.get_or_404(id)
        db.session.delete(order_to_delete)
        db.session.commit()
        return """<script>alert('Order Deleted Successfully'); window.location.href='/admin';</script>"""
    except Exception as e:
        return f"Error deleting order: {e}"

if __name__ == '__main__':
    app.run(debug=True)