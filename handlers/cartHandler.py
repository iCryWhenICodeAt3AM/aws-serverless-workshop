import json
import boto3
import os
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
cart_table = dynamodb.Table('user_carts_rey')
inventory_table = dynamodb.Table(os.getenv('PRODUCTS_INVENTORY_TABLE'))

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

def add_to_cart(event, context):
    user_id = event['pathParameters']['user_id']
    product = json.loads(event['body'], parse_float=Decimal)
    product_id = product['product_id']
    product_quantity = Decimal(product['quantity'])

    # Fetch the current cart
    response = cart_table.get_item(Key={'user_id': user_id})
    cart = response.get('Item', {}).get('cart', [])

    # Check if the product already exists in the cart
    existing_product = next((item for item in cart if item['product_id'] == product_id), None)
    if existing_product:
        existing_product['quantity'] = Decimal(existing_product['quantity']) + product_quantity
    else:
        cart.append(product)

    # Update the cart in the database
    response = cart_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression="SET cart = :cart",
        ExpressionAttributeValues={
            ':cart': cart
        },
        ReturnValues="UPDATED_NEW"
    )

    return {
        'statusCode': 200,
        'body': json.dumps(response['Attributes']['cart'], default=decimal_default),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def get_cart(event, context):
    user_id = event['pathParameters']['user_id']

    response = cart_table.get_item(
        Key={'user_id': user_id}
    )

    cart = response.get('Item', {}).get('cart', [])

    # Convert any Decimal to string
    cart = json.loads(json.dumps(cart, default=decimal_default))

    return {
        'statusCode': 200,
        'body': json.dumps(cart),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def checkout(event, context):
    user_id = event['pathParameters']['user_id']

    # Fetch the current cart
    response = cart_table.get_item(Key={'user_id': user_id})
    cart = response.get('Item', {}).get('cart', [])

    if not cart:
        return {
            'statusCode': 400,
            'body': json.dumps({"message": "Cart is empty"}),
            'headers': {
                'Content-Type': 'application/json',
            },
        }

    # Get the current local time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Process each item in the cart
    for item in cart:
        inventory_item = {
            "product_id": item['product_id'],
            "quantity": -Decimal(item['quantity']),  # Negative quantity for purchase
            "remark": "Purchased item!",
            "timestamp": current_time
        }
        try:
            inventory_table.put_item(Item=inventory_item)
        except Exception as e:
            print(f"❌ Error adding inventory item: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({"message": f"Error processing item {item['product_id']}: {str(e)}"}),
                'headers': {
                    'Content-Type': 'application/json',
                },
            }

    # Clear the cart after checkout
    cart_table.update_item(
        Key={'user_id': user_id},
        UpdateExpression="SET cart = :empty_cart",
        ExpressionAttributeValues={':empty_cart': []},
        ReturnValues="UPDATED_NEW"
    )

    return {
        'statusCode': 200,
        'body': json.dumps({"message": "Checkout successful"}),
        'headers': {
            'Content-Type': 'application/json',
        },
    }
