import os
import json
from datetime import datetime
from decimal import Decimal
from gateways.awsGateway import AWSGateway
from models.padeliverModel import PadeliverModel
from handlers.cartHandler import get_cart
import boto3
from boto3.dynamodb.conditions import Key

aws_gateway = AWSGateway()
padeliver_model = PadeliverModel()
dynamodb = boto3.resource('dynamodb')
padeliver_table = dynamodb.Table('PADELIVER_PRODUCTS_TABLE')  # Replace with the actual table name or environment variable

def get_padeliver_products(event, context):
    """Handler for retrieving all padeliver products."""
    try:
        response = padeliver_table.scan()
        items = response.get('Items', [])
        return {
            "statusCode": 200,
            'headers': {'Content-Type': 'application/json',},
            "body": json.dumps(items)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error retrieving products: {str(e)}"})
        }

def process_padeliver_csv(event, context):
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    for record in event['Records']:
        key = record['s3']['object']['key']
        content = aws_gateway.get_s3_object(bucket_name, key)
        if content:
            if key.startswith('for_padeliver_create/'):
                products = padeliver_model.process_create_csv(content)
                aws_gateway.batch_create_products(products)
            elif key.startswith('for_padeliver_delete/'):
                product_ids = padeliver_model.process_delete_csv(content)
                aws_gateway.batch_delete_products(product_ids)
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'CSV processed successfully'}),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def get_padeliver_product_names(event, context):
    product_names = aws_gateway.get_product_names()
    return {
        'statusCode': 200,
        'body': json.dumps(product_names),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def view_padeliver_product_by_id_or_name(event, context):
    """Handler for viewing a padeliver product by product_id or item header."""
    headers = event.get("headers", {})
    product_id = headers.get("product_id")
    item = headers.get("item")

    if product_id == "default":
        product_id = None
    else:
        item = None

    if not product_id and not item:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing product_id or item header"})
        }

    if item:
        try:
            product_name_item = aws_gateway.get_product_name(item)
            if product_name_item:
                product_id = product_name_item["product_id"]
            else:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "Item not found"})
                }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": f"Error searching item table: {str(e)}"})
            }

    if not product_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Invalid product_id"})
        }
    response = aws_gateway.view_product(product_id)
    response["headers"] = {"Content-Type": "application/json"}
    return response

def view_padeliver_product_by_id_or_name_with_user(event, context):
    """Handler for viewing a padeliver product by product_id or item header with user-specific cart details."""
    headers = event.get("headers", {})
    user_id = event['pathParameters']['user_id']
    product_id = headers.get("product_id")
    item = headers.get("item")

    if product_id == "default":
        product_id = None
    else:
        item = None

    if not product_id and not item:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing product_id or item header"})
        }

    if item:
        try:
            product_name_item = aws_gateway.get_product_name(item)
            if product_name_item:
                product_id = product_name_item["product_id"]
            else:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "Item not found"})
                }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": f"Error searching item table: {str(e)}"})
            }

    if not product_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Invalid product_id"})
        }

    # Fetch the product details
    response = aws_gateway.view_product(product_id)
    product = json.loads(response["body"])

    # Fetch the user's cart
    cart_response = get_cart({"pathParameters": {"user_id": user_id}}, context)
    cart_data = json.loads(cart_response["body"])

    # Ensure cart_data is a dictionary and extract the cart list
    cart = cart_data.get("cart", []) if isinstance(cart_data, dict) else []

    product["in_user_cart"] = 0

    # Find the matching product in the user's cart and append the quantity
    for cart_item in cart:
        if cart_item.get("product_id") == product_id:
            product["in_user_cart"] = int(cart_item["quantity"])  # Convert to int
            break

    response["body"] = json.dumps(product, default=aws_gateway.decimal_default)
    response["headers"] = {"Content-Type": "application/json"}
    return response

def add_padeliver_inventory(event, context):
    """Handler for adding inventory to a padeliver product."""
    body = json.loads(event.get("body", "{}"), parse_float=Decimal)
    product_id = body.get("product_id")
    quantity = body.get("quantity")
    remark = body.get("remark", "Default remark.")

    if not product_id or quantity is None:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Invalid input: Missing product_id or quantity"})
        }

    # Check if the product_id exists in the padeliver table
    if not aws_gateway.product_exists(product_id):
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Product not found"})
        }

    # Get the current local time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create the inventory item
    inventory_item = {
        "product_id": product_id,
        "quantity": int(quantity),
        "remark": remark,
        "datetime": current_time
    }

    # Add the inventory item to the inventory table
    try:
        aws_gateway.add_inventory_item(inventory_item)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Inventory added successfully"})
        }
    except Exception as e:
        print(f"❌ Error adding inventory: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error adding inventory: {str(e)}"})}
