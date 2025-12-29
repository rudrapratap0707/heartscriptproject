import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Render Database Path
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model (Wahi jo aapka tha)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    total = db.Column(db.String(20), nullable=False)
    items = db.Column(db.Text, nullable=False)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return render_template('index.html')

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
        return jsonify({"status": "success", "id": new_order.id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin')
def admin():
    all_orders = Order.query.order_by(Order.date_ordered.desc()).all()
    return render_template('admin.html', orders=all_orders)

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
    with app.app_context():
        db.create_all()
    # Render requirements
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)