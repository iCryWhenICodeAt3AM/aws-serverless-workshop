import json
import csv
from decimal import Decimal
from gateways import dynamodb_gateway, s3_gateway, sqs_gateway
from utils.aws_resources import logger, DecimalEncoder

# ---------- Single Product Operations ----------

def create_product(event):
    """Create a product."""
    body = json.loads(event.get("body", "{}"), parse_float=Decimal) # the payload parse the Decimal
    
    if not body or "product_id" not in body: # if there is no product id
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid input: Missing product_id"})}
    logger.info(f"Creating product: {body}") # logs
    
    dynamodb_gateway.save_product(body) # save the product
    
    # sqs
    try:
        sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Create a Product! Item: {body}")
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        
    return {"statusCode": 200, "body": json.dumps({"message": "Product created successfully", "product": body}, cls=DecimalEncoder)}

def get_all_products():
    """Retrieve all products."""
    items = dynamodb_gateway.scan_products() # get all products
    
    #sqs
    try:
        sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Get All Products! Items: {items}")
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        
    return {"statusCode": 200, "body": json.dumps({"items": items, "status": "success"}, cls=DecimalEncoder)}

def view_product(product_id):
    """Retrieve a single product by ID."""
    if not product_id: # if there is no product id
        return {"statusCode": 400, "body": json.dumps({"message": "Missing product_id"})}
        
    item = dynamodb_gateway.get_product(product_id) # get the product
    
    if not item: # if there is no product found
        return {"statusCode": 404, "body": json.dumps({"message": "Product not found"})}
    
    # sqs    
    try:
        sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Get a Product! {product_id}")
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        
    return {"statusCode": 200, "body": json.dumps(item, cls=DecimalEncoder)}

def edit_product(data):
    """Edit an existing product."""
    product_id = data.get("product_id") # get product id from the payload
    
    if not product_id: # if there is no product id in the payload
        return {"statusCode": 400, "body": json.dumps({"message": "Missing product_id"})}
    
    # data prep and send
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in data if k != "product_id") # organize a query, e.g. SET key = :item, ...
    expression_values = {f":{k}": v for k, v in data.items() if k != "product_id"} # create a dictionary for items e.g. :item : item_name, ...
    dynamodb_gateway.update_product(product_id, update_expression, expression_values) # update the product
    
    # sqs
    try:
        sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Edited a Product! Item: {product_id}")
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        
    return {"statusCode": 200, "body": json.dumps({"message": "Product updated successfully"})}

def delete_product(product_id):
    """Delete a product."""
    if not product_id: # if no product id passed
        return {"statusCode": 400, "body": json.dumps({"message": "Missing product_id"})}
        
    dynamodb_gateway.delete_product(product_id) # delete the product
    
    # sqs
    try:
        sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Deleted a Product! Item: {product_id}")
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        
    return {"statusCode": 200, "body": json.dumps({"message": f"Product {product_id} deleted successfully"})}

# ---------- Batch Operations ----------

def batch_create_products_model(event):
    """Batch create products from an S3 CSV file."""
    logger.info("Batch create model triggered.")
    
    bucket, local_filename, error = s3_gateway.download_file_from_s3(event, "for_create") # download the file from the folder
    
    if error: # incase of errors
        return error
        
    # opening the file and rendering csv to dictionary
    with open(local_filename, "r") as f:
        csv_reader = csv.DictReader(f)
        items = list(csv_reader)
        
    if not items: # if there are no items parsed
        return {"statusCode": 400, "body": json.dumps({"message": "CSV file is empty"})}
        
    dynamodb_gateway.batch_create_products(items) # start creating the items
    
    logger.info(f"Inserted {len(items)} products successfully.") # logs
    
    # sqs
    try:
        sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Batch Create Triggered! Items: {items}")
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        
    return {"statusCode": 200, "body": json.dumps({"message": f"{len(items)} products created."})}

# same concept as batch create
def batch_delete_products_model(event):
    """Batch delete products from an S3 CSV file."""
    logger.info("Batch delete model triggered.")
    bucket, local_filename, error = s3_gateway.download_file_from_s3(event, "for_delete")
    if error:
        return error
    with open(local_filename, "r") as f:
        reader = csv.reader(f)
        product_ids = [row[0] for row in reader if row]
    if not product_ids:
        return {"statusCode": 400, "body": json.dumps({"message": "No product IDs found"})}
    dynamodb_gateway.batch_delete_products(product_ids)
    logger.info(f"Deleted {len(product_ids)} products successfully.")
    try:
        sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Batch delete triggered! Items: {product_ids}")
    except Exception:
        return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
    return {"statusCode": 200, "body": json.dumps({"message": f"Deleted {len(product_ids)} products"})}
