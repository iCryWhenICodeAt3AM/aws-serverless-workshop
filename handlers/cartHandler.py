import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
cart_table = dynamodb.Table('user_carts_rey')

def add_to_cart(event, context):
    user_id = event['pathParameters']['user_id']
    product = json.loads(event['body'], parse_float=Decimal)
    product_id = product['product_id']
    product_quantity = product['quantity']

    # Fetch the current cart
    response = cart_table.get_item(Key={'user_id': user_id})
    cart = response.get('Item', {}).get('cart', [])

    # Check if the product already exists in the cart
    existing_product = next((item for item in cart if item['product_id'] == product_id), None)
    if existing_product:
        existing_product['quantity'] += product_quantity
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
        'body': json.dumps(response['Attributes']['cart']),
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
    cart = json.loads(json.dumps(cart, default=str))

    return {
        'statusCode': 200,
        'body': json.dumps(cart),
        'headers': {
            'Content-Type': 'application/json',
        },
    }
