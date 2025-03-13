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
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

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

pnconfig = PNConfiguration()
pnconfig.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY')
pnconfig.publish_key = os.getenv('PUBNUB_PUBLISH_KEY')
pnconfig.uuid = "server-uuid"
pubnub = PubNub(pnconfig)

@app.route('/')
def hello_world():
    return render_template('index.html', web_chat_token=os.getenv('WEB_CHAT_TOKEN'), web_host_url=os.getenv('WEB_HOST_URL'), unique_site_id=os.getenv('UNIQUE_SITE_ID'), api_base_url=API_BASE_URL)

@app.route('/restaurant.html')
def restaurant_page():
    return render_template('restaurant.html', web_chat_token=os.getenv('WEB_CHAT_TOKEN'), web_host_url=os.getenv('WEB_HOST_URL'), unique_site_id=os.getenv('UNIQUE_SITE_ID'), api_base_url=API_BASE_URL)

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
            # pubnub.publish().channel(user_id).message({"action": "add_to_cart", "status": "success"}).sync()
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

if __name__ == '__main__':
    app.run(debug=True)