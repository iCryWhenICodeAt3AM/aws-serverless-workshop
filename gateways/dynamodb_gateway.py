from utils.aws_resources import aws_resources, logger
import json

def save_product(product):
    """Insert a single product into DynamoDB."""
    aws_resources.products_table.put_item(Item=product)

def scan_products():
    """Retrieve all products from DynamoDB."""
    response = aws_resources.products_table.scan()
    return response.get("Items", [])

def get_product(product_id):
    """Get a single product by ID."""
    response = aws_resources.products_table.get_item(Key={"product_id": product_id})
    return response.get("Item")

def update_product(product_id, update_expression, expression_attribute_values):
    """Update a product in DynamoDB."""
    aws_resources.products_table.update_item(
        Key={"product_id": product_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

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
    aws_resources.product_inventory_table.put_item(Item=item)

def get_product_inventory(product_id):
    """Get all inventory records for a product by ID."""
    response = aws_resources.product_inventory_table.query(
        KeyConditionExpression="product_id = :product_id",
        ExpressionAttributeValues={":product_id": product_id}
    )
    return response.get("Items", [])

def update_product_quantity(product_id, quantity):
    """Update the quantity of a product in DynamoDB."""
    product = get_product(product_id)
    if product:
        new_quantity = product.get("quantity", 0) + quantity
        update_expression = "SET quantity = :quantity"
        expression_attribute_values = {":quantity": new_quantity}
        update_product(product_id, update_expression, expression_attribute_values)
        return {"statusCode": 200, "body": json.dumps({"message": "Product quantity updated successfully"})}
    else:
        logger.info(f"Product with ID {product_id} not found.")
        return {"statusCode": 404, "body": json.dumps({"message": f"Product with ID {product_id} not found."})}
