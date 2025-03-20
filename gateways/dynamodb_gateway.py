from utils.aws_resources import aws_resources, logger
import json
from datetime import datetime
from decimal import Decimal

def save_product(product):
    """Insert a single product into DynamoDB."""
    aws_resources.products_table.put_item(Item=product)

def scan_products():
    """Retrieve all products from DynamoDB."""
    response = aws_resources.products_table.scan()
    return response.get("Items", [])

def get_product(product_id):
    """Get a single product by ID and sum its quantities from the inventory table."""
    # Ensure the key attribute name matches the table schema
    response = aws_resources.products_table.get_item(Key={"product_id": product_id})
    product = response.get("Item")
    
    if not product:
        return None

    # Get all inventory records for the product
    inventory_response = aws_resources.product_inventory_table.query(
        KeyConditionExpression="product_id = :product_id",
        ExpressionAttributeValues={":product_id": product_id}
    )
    inventory_items = inventory_response.get("Items", [])
    
    # Calculate the total quantity, ensuring type conversion to Decimal
    total_quantity = sum(Decimal(item.get("quantity", 0)) for item in inventory_items)
    
    # Add the total quantity to the product
    product["total_quantity"] = total_quantity if inventory_items else Decimal(0)
    return product

def get_product_name(product_name):
    """Get a product ID by product name."""
    try:
        response = aws_resources.product_name_table.get_item(Key={"product_name": product_name})
        item = response.get("Item")
        if item:
            logger.info(f"Product name '{product_name}' found with ID: {item.get('product_id')}")
        else:
            logger.info(f"Product name '{product_name}' not found.")
        return item
    except Exception as e:
        logger.error(f"Error retrieving product name '{product_name}': {e}")
        return None

def get_all_product_names():
    """Retrieve all product names from the product_name_table."""
    response = aws_resources.product_name_table.scan()
    return response.get("Items", [])

def update_product(product_id, update_expression, expression_attribute_values):
    """Update a product in DynamoDB."""
    product = get_product(product_id)
    if product:
        aws_resources.products_table.update_item(
            Key={"product_id": product_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return {"statusCode": 200, "body": json.dumps({"message": "Product updated successfully"})}
    else:
        return {"statusCode": 404, "body": json.dumps({"message": f"Product with ID {product_id} not found."})}

def delete_product(product_id):
    """Delete a product from DynamoDB."""
    aws_resources.products_table.delete_item(Key={"product_id": product_id})

def batch_create_products(items):
    """Batch insert products using DynamoDB batch_writer."""
    with aws_resources.products_table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

def batch_delete_products(product_ids):
    """Batch delete products using DynamoDB batch_writer."""
    with aws_resources.products_table.batch_writer() as batch:
        for pid in product_ids:
            batch.delete_item(Key={"product_id": pid})

def save_product_inventory(item):
    """Insert a single product inventory record into DynamoDB."""
    # Check if the product exists in the products table
    product_id = item.get("product_id")
    if not get_product(product_id):
        return {"statusCode": 404, "body": json.dumps({"message": f"Product with ID {product_id} not found."})}

    # Get the current local time in ISO format
    item["datetime"] = datetime.now().isoformat()
    
    if "remarks" not in item:
        item["remarks"] = "Default remarks."

    # Insert item into DynamoDB
    aws_resources.product_inventory_table.put_item(Item=item)
    return {"statusCode": 200, "body": json.dumps({"message": "Product inventory record saved successfully"})}

def update_product_quantity(product_id, quantity):
    """Update the quantity of a product in DynamoDB."""
    product = get_product(product_id)
    if product:
        new_quantity = product.get("quantity", 0) + quantity
        update_expression = "SET quantity = :quantity"
        expression_attribute_values = {":quantity": new_quantity}
        aws_resources.products_table.update_item(
            Key={"product_id": product_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return {"statusCode": 200, "body": json.dumps({"message": "Product quantity updated successfully"})}
    else:
        logger.info(f"Product with ID {product_id} not found.")
        return {"statusCode": 404, "body": json.dumps({"message": f"Product with ID {product_id} not found."})}

def save_product_name(item):
    """Insert a product name and ID into DynamoDB."""
    aws_resources.product_name_table.put_item(Item=item)
