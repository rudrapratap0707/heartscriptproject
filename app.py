import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Render ke liye path define karna
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
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
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error: Template not found. Make sure index.html is inside 'templates' folder. Full error: {str(e)}"

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
