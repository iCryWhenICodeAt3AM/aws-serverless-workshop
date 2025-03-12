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

app = Flask(__name__, static_folder='static')
app.secret_key = 'supersecretkey'
product_model = FlaskProductModel()

dynamodb = boto3.resource('dynamodb')
padeliver_table_name = os.getenv('PADELIVER_PRODUCTS_TABLE')

if not padeliver_table_name:
    raise ValueError("PADELIVER_PRODUCTS_TABLE environment variable is not set")

padeliver_table = dynamodb.Table(padeliver_table_name)

@app.route('/')
def hello_world():
    return render_template('index.html', web_chat_token=os.getenv('WEB_CHAT_TOKEN'), web_host_url=os.getenv('WEB_HOST_URL'), unique_site_id=os.getenv('UNIQUE_SITE_ID'))

@app.route('/restaurant.html')
def restaurant_page():
    return render_template('restaurant.html', web_chat_token=os.getenv('WEB_CHAT_TOKEN'), web_host_url=os.getenv('WEB_HOST_URL'), unique_site_id=os.getenv('UNIQUE_SITE_ID'))

@app.route('/api/products')
def get_products():
    try:
        response = padeliver_table.scan()
        products = response.get('Items', [])
        return jsonify(products)
    except Exception as e:
        print(f"Error fetching products: {e}")
        return jsonify([])

@app.route('/api/cart', methods=['GET', 'POST'])
def cart():
    if 'cart' not in session:
        session['cart'] = []

    if request.method == 'POST':
        product = request.json
        session['cart'].append(product)
        session.modified = True

    return jsonify(session['cart'])

if __name__ == '__main__':
    app.run(debug=True)