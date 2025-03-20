import os
import json
import logging
from datetime import datetime
from decimal import Decimal
from gateways import dynamodb_gateway
from gateways.awsGateway import AWSGateway
from models.padeliverModel import PadeliverModel
from handlers.cartHandler import get_cart
import boto3
from boto3.dynamodb.conditions import Key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Handler for processing CSV files uploaded to S3 for batch creation or deletion of Pa-deliver products."""
    bucket_name = os.getenv('S3_BUCKET_NAME')

    for record in event['Records']:
        key = record['s3']['object']['key']
        logger.info(f"Processing file from S3: bucket={bucket_name}, key={key}")

        # Fetch the content of the uploaded file
        content = aws_gateway.get_s3_object(bucket_name, key)
        if content:
            try:
                if key.startswith('for_padeliver_create/'):
                    # Process the CSV for batch creation
                    products = padeliver_model.process_create_csv(content)
                    aws_gateway.batch_create_products(products)
                    logger.info(f"Batch created {len(products)} products from file: {key}")
                elif key.startswith('for_padeliver_delete/'):
                    # Process the CSV for batch deletion
                    product_ids = padeliver_model.process_delete_csv(content)
                    aws_gateway.batch_delete_products(product_ids)
                    logger.info(f"Batch deleted {len(product_ids)} products from file: {key}")
            except Exception as e:
                logger.error(f"Error processing file {key}: {e}")
        else:
            logger.error(f"Failed to fetch content for file: {key}")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'CSV files processed successfully'}),
        'headers': {'Content-Type': 'application/json'},
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
            "body": json.dumps({"message": f"Error adding inventory: {str(e)}"})
        }

def get_padeliver_products_with_stock(event, context):
    """Handler to fetch Pa-deliver products along with their stock."""
    try:
        # Fetch all products from the PADELIVER_PRODUCTS_TABLE
        products = aws_gateway.scan_padeliver_products()

        # Fetch stock for each product
        for product in products:
            product_id = product["product_id"]
            inventory_data = aws_gateway.get_product_inventory(product_id)
            product["stock"] = int(inventory_data["total_quantity"])  # Convert Decimal to int

        # Convert all Decimal values in the products list to JSON-serializable types
        def decimal_to_serializable(obj):
            if isinstance(obj, Decimal):
                return int(obj)  # Convert Decimal to int
            raise TypeError

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(products, default=decimal_to_serializable)
        }
    except Exception as e:
        logger.error(f"Error fetching Pa-deliver products with stock: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error fetching Pa-deliver products with stock: {str(e)}"})
        }

def add_padeliver_product(event, context):
    """Handler for adding a new Pa-deliver product."""
    body = json.loads(event.get("body", "{}"), parse_float=Decimal)
    product_id = body.get("product_id")
    item = body.get("item")
    description = body.get("description")
    price = body.get("price")
    brand = body.get("brand")
    category = body.get("category")

    # Validate input
    if not product_id or not item or not description or not price or not brand or not category:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing required fields: product_id, item, description, price, brand, or category"})
        }

    # Check if product_id or item already exists
    if aws_gateway.product_exists(product_id):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Product ID already exists", "invalid_field": "product_id"})
        }

    existing_product_by_name = aws_gateway.get_product_name(item)
    if existing_product_by_name:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Product name already exists", "invalid_field": "item"})
        }

    # Create the new product
    new_product = {
        "product_id": product_id,
        "item": item,
        "product_description": description,
        "price": price,  # Ensure price is stored as a string
        "brand": brand,  # Include brand
        "category": category,  # Include category
    }

    try:
        aws_gateway.add_product(new_product)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Product added successfully", "product": new_product})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error adding product: {str(e)}"})
        }

def edit_padeliver_product(event, context):
    """Handler for editing a Pa-deliver product and updating related inventory."""
    body = json.loads(event.get("body", "{}"), parse_float=Decimal)
    old_product_id = body.get("old_product_id")
    new_product_id = body.get("new_product_id")
    updates = {key: value for key, value in body.items() if key not in ["old_product_id", "new_product_id"]}

    if not old_product_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "old_product_id must be provided"})
        }

    try:
        # Fetch the old product
        product = aws_gateway.view_product(old_product_id)
        if product["statusCode"] != 200:
            return product

        product_data = json.loads(product["body"])

        # If a new product_id is provided, move the product to the new product_id
        if new_product_id:
            # Check if the new product_id already exists
            if aws_gateway.product_exists(new_product_id):
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "New product_id already exists", "invalid_field": "new_product_id"})
                }

            # Update the product_id and apply updates
            product_data["product_id"] = new_product_id
            product_data.update(updates)

            # Delete the old product
            aws_gateway.delete_product(old_product_id)

            # Add the updated product with the new product_id
            aws_gateway.add_product(product_data)

            # Update all inventory records with the new product_id
            inventory_data = aws_gateway.get_product_inventory(old_product_id)
            for inventory_item in inventory_data["inventory_items"]:
                inventory_item["product_id"] = new_product_id
                aws_gateway.add_inventory_item(inventory_item)

            logger.info(f"Product ID changed from {old_product_id} to {new_product_id} with updates: {updates}")
        else:
            # Apply updates to the existing product_id
            product_data.update(updates)
            aws_gateway.add_product(product_data)
            logger.info(f"Product {old_product_id} updated with: {updates}")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Product and inventory updated successfully"})
        }
    except Exception as e:
        logger.error(f"Error editing product {old_product_id}: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error editing product: {str(e)}"})
        }

def delete_padeliver_product(event, context):
    """Handler for deleting a Pa-deliver product and its related inventory."""
    body = json.loads(event.get("body", "{}"))
    product_id = body.get("product_id")

    if not product_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing product_id"})
        }

    try:
        # Delete the product
        aws_gateway.delete_product(product_id)
        logger.info(f"Product deleted successfully: {product_id}")

        # Delete all related inventory records
        inventory_data = aws_gateway.get_product_inventory(product_id)
        logger.info(f"Product inventory deleted successfully: {inventory_data}")
        for inventory_item in inventory_data["inventory_items"]:
            aws_gateway.delete_inventory_item(
                product_id=inventory_item["product_id"],
                datetime=inventory_item["datetime"]
            )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Product and related inventory deleted successfully"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error deleting product: {str(e)}"})
        }

def batch_create_padeliver_products(event, context):
    """Handler for batch creating Pa-deliver products."""
    try:
        # Parse the request body
        body = json.loads(event.get("body", "[]"), parse_float=Decimal)
        if not isinstance(body, list) or not body:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Invalid input: Expected a non-empty list of products"})
            }

        # Validate and process each product
        for product in body:
            if not product.get("product_id") or not product.get("item"):
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "Each product must have a product_id and item"})
                }

        # Batch create products
        aws_gateway.batch_create_products(body)
        logger.info(f"Batch created {len(body)} Pa-deliver products successfully.")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Batch created {len(body)} products successfully"})
        }
    except Exception as e:
        logger.error(f"Error batch creating Pa-deliver products: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error batch creating products: {str(e)}"})
        }
