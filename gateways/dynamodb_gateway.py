from utils.aws_resources import PRODUCTS_TABLE, logger

def save_product(product):
    """Insert a single product into DynamoDB."""
    PRODUCTS_TABLE.put_item(Item=product)

def scan_products():
    """Retrieve all products from DynamoDB."""
    response = PRODUCTS_TABLE.scan()
    return response.get("Items", [])

def get_product(product_id):
    """Get a single product by ID."""
    response = PRODUCTS_TABLE.get_item(Key={"product_id": product_id})
    return response.get("Item")

def update_product(product_id, update_expression, expression_attribute_values):
    """Update a product in DynamoDB."""
    PRODUCTS_TABLE.update_item(
        Key={"product_id": product_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

def delete_product(product_id):
    """Delete a product from DynamoDB."""
    PRODUCTS_TABLE.delete_item(Key={"product_id": product_id})

def batch_create_products(items):
    """Batch insert products using DynamoDB batch_writer."""
    with PRODUCTS_TABLE.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

def batch_delete_products(product_ids):
    """Batch delete products using DynamoDB batch_writer."""
    with PRODUCTS_TABLE.batch_writer() as batch:
        for pid in product_ids:
            batch.delete_item(Key={"product_id": pid})
