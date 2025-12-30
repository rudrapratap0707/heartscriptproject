import os
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import certifi
from flask_cors import CORS # Dusre phone se connection allow karne ke liye

app = Flask(__name__)
CORS(app) # Sabhi origins se request allow karega

# MongoDB Connection (Render ke MONGO_URI variable se link uthayega)
MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['heartscript_db'] # Aapka database naam
orders_collection = db['orders'] # Aapka collection (table) naam

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        data = request.json
        new_order = {
            "name": data['name'],
            "phone": data['phone'],
            "address": data['address'],
            "total": data['total'],
            "items": data['items'],
            "date_ordered": datetime.utcnow()
        }
        
        # MongoDB mein data insert karna
        result = orders_collection.insert_one(new_order)
        
        return jsonify({"status": "success", "id": str(result.inserted_id)})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/admin')
def admin():
    # Saare orders fetch karna (Latest pehle)
    all_orders = list(orders_collection.find().sort("date_ordered", -1))
    return render_template('admin.html', orders=all_orders)

@app.route('/delete_order/<id>')
def delete_order(id):
    from bson.objectid import ObjectId
    try:
        orders_collection.delete_one({"_id": ObjectId(id)})
        return """<script>alert('Order Deleted Successfully'); window.location.href='/admin';</script>"""
    except Exception as e:
        return f"Error deleting order: {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
