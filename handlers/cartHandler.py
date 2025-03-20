import json
import boto3
import os
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
cart_table = dynamodb.Table('user_carts_rey')
inventory_table = dynamodb.Table(os.getenv('PRODUCTS_INVENTORY_TABLE'))
orders_table = dynamodb.Table(os.getenv('PADELIVER_ORDERS_TABLE'))  # New table for orders
s3 = boto3.client('s3')
s3_bucket_name = os.getenv('S3_BUCKET_NAME')

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

    # Add a message indicating if the cart is empty or not
    message = "Cart is empty" if not cart else "Cart contains items"

    return {
        'statusCode': 200,
        'body': json.dumps({"message": message, "cart": cart}),
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

    # Push all cart contents to inventory as negative quantities
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in cart:
        inventory_item = {
            "product_id": item['product_id'],
            "quantity": -Decimal(item['quantity']),  # Negative quantity for purchase
            "remark": "Purchased item!",
            "datetime": current_time  # Ensure the datetime key is included
        }
        inventory_table.put_item(Item=inventory_item)

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

def get_formatted_cart(event, context):
    user_id = event['pathParameters']['user_id']

    # Fetch the current cart
    response = cart_table.get_item(Key={'user_id': user_id})
    cart = response.get('Item', {}).get('cart', [])

    if not cart:
        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Cart is empty"}),
            'headers': {
                'Content-Type': 'application/json',
            },
        }

    formatted_items = []
    total_price = Decimal(0)

    for item in cart:
        item_total = Decimal(item['quantity']) * Decimal(item['price'])
        formatted_items.append(f"{item['quantity']}x {item['item']}: {item_total:.2f}")
        total_price += item_total

    formatted_cart = {
        "items": formatted_items,
        "total": f"{total_price:.2f}"
    }

    return {
        'statusCode': 200,
        'body': json.dumps(formatted_cart),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def place_order(event, context):
    """Handler for placing an order."""
    user_id = event['pathParameters']['user_id']  # user_id is equivalent to customer_name

    # Fetch the current cart
    response = cart_table.get_item(Key={'user_id': user_id})
    cart = response.get('Item', {}).get('cart', [])

    if not cart:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Cart is empty"})
        }

    try:
        # Get the current system datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create an order ID
        order_id = f"ORD-{int(datetime.now().timestamp())}"

        # Prepare the order data
        order_data = {
            "order_id": order_id,  # Primary key
            "customer_name": user_id,  # user_id is stored as customer_name
            "items": cart,
            "status": "Preparing",
            "order_datetime": current_time
        }

        # Store the order in the orders table
        orders_table.put_item(Item=order_data)

        # Reduce inventory for each product in the cart
        for item in cart:
            inventory_payload = {
                "product_id": item['product_id'],
                "quantity": -Decimal(item['quantity']),  # Negative quantity for stock-out
                "remark": f"Stock-out: Purchase made by {order_id}",
                "datetime": current_time
            }
            inventory_table.put_item(Item=inventory_payload)

        # Clear the cart after placing the order
        cart_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression="SET cart = :empty_cart",
            ExpressionAttributeValues={':empty_cart': []},
            ReturnValues="UPDATED_NEW"
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Order placed successfully", "order_id": order_id})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error placing order: {str(e)}"})
        }

def get_orders(event, context):
    """Handler for retrieving all orders for a user."""
    user_id = event['pathParameters']['user_id']  # user_id is equivalent to customer_name

    try:
        # Query the orders table for the user's orders
        response = orders_table.query(
                KeyConditionExpression=Key('customer_name').eq(user_id)
            )

        orders = response.get('Items', [])

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"orders": orders}, default=decimal_default)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error retrieving orders: {str(e)}"})
        }

def get_all_orders(event, context):
    """Handler for retrieving all orders."""
    try:
        # Scan the orders table to fetch all orders
        response = orders_table.scan()
        orders = response.get('Items', [])

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"orders": orders}, default=decimal_default)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error retrieving all orders: {str(e)}"})
        }

def update_order_status(event, context):
    """Handler for updating the status of a specific order."""
    try:
        # ✅ Parse request body
        body = json.loads(event.get('body', '{}'))
        order_id = body.get('order_id')
        customer_name = body.get('customer_name')  # Equivalent to user_id
        new_status = body.get('status')

        # ✅ Validate request payload
        if not order_id or not customer_name or not new_status:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Missing required fields: order_id, customer_name, or status"})
            }

        # ✅ Ensure order exists and belongs to the correct customer
        existing_order = orders_table.get_item(Key={'order_id': order_id})
        
        if 'Item' not in existing_order:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Order not found"})
            }

        if existing_order['Item'].get('customer_name') != customer_name:
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Unauthorized: Order does not belong to the specified customer"})
            }

        # ✅ Update order status
        response = orders_table.update_item(
            Key={'order_id': order_id},
            UpdateExpression="SET #status = :new_status",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':new_status': new_status},
            ReturnValues="UPDATED_NEW"
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "Order status updated successfully",
                "updatedAttributes": response.get('Attributes', {})
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error updating order status: {str(e)}"})
        }

def generate_receipt(event, context):
    """Handler for generating a receipt for a specific order."""
    body = json.loads(event['body'])
    order_id = body.get('order_id')
    customer_name = body.get('customer_name')  # Equivalent to user_id

    if not order_id or not customer_name:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing required fields: order_id or customer_name"})
        }

    try:
        # Fetch the order from the orders table
        response = orders_table.get_item(Key={'order_id': order_id})
        order = response.get('Item')

        if not order or order.get('customer_name') != customer_name:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Order not found or does not belong to the customer"})
            }

        # Generate receipt content
        receipt_content = f"Order Receipt\n\nOrder ID: {order_id}\nCustomer Name: {customer_name}\n"
        receipt_content += f"Order Date: {order['order_datetime']}\nStatus: {order['status']}\n\nItems:\n"

        for item in order['items']:
            receipt_content += f"- {item['quantity']}x {item['item']} @ {item['price']} each\n"

        receipt_content += f"\nTotal Items: {len(order['items'])}\n"

        # Upload the receipt to S3
        receipt_key = f"receipts/{order_id}.txt"
        s3.put_object(
            Bucket=s3_bucket_name,
            Key=receipt_key,
            Body=receipt_content,
            ContentType='text/plain'
        )

        receipt_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{receipt_key}"

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Receipt generated successfully", "receipt_url": receipt_url})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error generating receipt: {str(e)}"})
        }
