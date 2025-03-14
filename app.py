import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the virtual environment's site-packages directory to the Python path
venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
sys.path.append(venv_path)

from flask import Flask, render_template, jsonify, request, session
from models.flaskProductModel import FlaskProductModel
import boto3
import requests

app = Flask(__name__, static_folder='static')
app.secret_key = 'supersecretkey'
product_model = FlaskProductModel()

dynamodb = boto3.resource('dynamodb')
padeliver_table_name = os.getenv('PADELIVER_PRODUCTS_TABLE')

if not padeliver_table_name:
    raise ValueError("PADELIVER_PRODUCTS_TABLE environment variable is not set")

padeliver_table = dynamodb.Table(padeliver_table_name)

API_BASE_URL = os.getenv('API_BASE_URL')

if not API_BASE_URL:
    raise ValueError("API_BASE_URL environment variable is not set")

@app.route('/')
def hello_world():
    return render_template('index.html', web_chat_token=os.getenv('WEB_CHAT_TOKEN'), web_host_url=os.getenv('WEB_HOST_URL'), unique_site_id=os.getenv('UNIQUE_SITE_ID'), api_base_url=API_BASE_URL)

@app.route('/restaurant.html')
def restaurant_page():
    return render_template('restaurant.html', web_chat_token=os.getenv('WEB_CHAT_TOKEN'), web_host_url=os.getenv('WEB_HOST_URL'), unique_site_id=os.getenv('UNIQUE_SITE_ID'), api_base_url=API_BASE_URL)

@app.route('/signin.html')
def signin():
    """Render the sign-in page."""
    return render_template('signin.html')

@app.route('/api/products')
def get_products():
    try:
        response = padeliver_table.scan()
        products = response.get('Items', [])
        return jsonify(products)
    except Exception as e:
        print(f"Error fetching products: {e}")
        return jsonify([])

@app.route('/api/cart/<user_id>', methods=['GET', 'POST'])
def cart(user_id):
    if request.method == 'POST':
        product = request.json
        response = requests.post(f"{API_BASE_URL}/api/cart/{user_id}", json=product)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to add product to cart'}), response.status_code
    else:
        response = requests.get(f"{API_BASE_URL}/api/cart/{user_id}")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch cart'}), response.status_code

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        user_id = request.json.get('user_id')
        product = request.json.get('product')
        if not user_id or not product:
            return jsonify({'error': 'Missing user_id or product in request'}), 400

        print(f"Adding to cart: user_id={user_id}, product={product}")

        response = requests.post(f"{API_BASE_URL}/api/cart/{user_id}", json=product)
        if response.status_code == 200:
            cart = response.json()
            print(f"Successfully added to cart: {cart}")
            return jsonify(cart)
        else:
            print(f"Error in add_to_cart: {response.status_code} - {response.text}")
            return jsonify({'error': f"Failed to add product to cart: {response.text}"}), response.status_code
    except Exception as e:
        print(f"Error in add_to_cart: {e}")
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500

@app.route('/get_cart/<user_id>', methods=['GET'])
def get_cart(user_id):
    try:
        response = requests.get(f"{API_BASE_URL}/api/cart/{user_id}")
        if response.status_code == 200:
            cart = response.json()
            return jsonify(cart)
        else:
            print(f"Error in get_cart: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to fetch cart'}), response.status_code
    except Exception as e:
        print(f"Error in get_cart: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/product-names', methods=['GET'])
def get_product_names():
    try:
        response = padeliver_table.scan()
        products = response.get('Items', [])
        product_names = [{"id": product["product_id"], "name": product["item"]} for product in products]
        return jsonify(product_names)
    except Exception as e:
        print(f"Error fetching product names: {e}")
        return jsonify([])

@app.route('/logout', methods=['GET'])
def logout():
    """Clear the session and redirect to the sign-in page."""
    session.clear()  # Clear the session
    return jsonify({"message": "Logged out successfully", "redirect": "/signin.html"}), 200

@app.route('/api/cart/<user_id>/checkout', methods=['POST'])
def checkout(user_id):
    """Handle the checkout process for a user."""
    try:
        # Send a POST request to the checkout endpoint
        response = requests.post(f"{API_BASE_URL}/api/cart/{user_id}/checkout")
        if response.status_code == 200:
            checkout_data = response.json()
            print(f"Checkout successful for user {user_id}: {checkout_data}")
            return jsonify(checkout_data), 200
        else:
            print(f"Checkout failed for user {user_id}: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to process checkout'}), response.status_code
    except Exception as e:
        print(f"Error during checkout: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)