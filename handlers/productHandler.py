import json
import csv
from decimal import Decimal
from models.productModel import ProductModel
from utils.event_bridge import submit_product_creation_event
import boto3 #type: ignore

product_model = ProductModel()

def create_one_product(event, context):
    """Handler for creating a product."""
    response = product_model.create_product(event)
    if response["statusCode"] == 200:
        product = json.loads(response["body"])["product"]
        submit_product_creation_event(product)
    return response

def get_all_products_handler(event, context):
    """Handler for retrieving all products."""
    return product_model.get_all_products()

def product_modification(event, context):
    """
    Handler for product modification.
    Uses query parameters to determine the operation:
      - GET: view (requires product_id)
      - PUT: edit (requires product data in body)
      - DELETE: delete (requires product_id in query)
      - POST: update inventory (requires inventory data in body)
    """
    params = event.get("queryStringParameters", {}) or {}
    http_method = params.get("http_method", "").upper() or event.get("requestContext", {}).get("http", {}).get("method", "UNKNOWN")
    
    actions = {
        "GET": lambda: product_model.view_product(params.get("product_id")),
        "PUT": lambda: product_model.edit_product(json.loads(event.get("body", "{}"), parse_float=Decimal)),
        "DELETE": lambda: product_model.delete_product(params.get("product_id")),
        "POST": lambda: product_model.update_product_inventory(event)
    }
    
    action = actions.get(http_method, lambda: {"statusCode": 400, "body": json.dumps({"message": "Invalid action or HTTP method"})})
    return action()


#-----------REST API HANDLERS FOR FRESH CHAT----------------

def view_product_handler(event, context):
    """Handler for viewing a product by product_id or product_name header."""
    headers = event.get("headers", {})
    product_id = headers.get("product_id")
    product_name = headers.get("product_name")

    if not product_id and not product_name:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing product_id or product_name header"})
        }

    if product_name and product_name.lower() != "0":
        try:
            # Search the product_name_table for the product ID
            product_name_item = product_model.dynamodb_gateway.get_product_name(product_name)
            if product_name_item:
                product_id = product_name_item["product_id"]
            else:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"message": "Product name not found"})
                }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": f"Error searching product name table: {str(e)}"})
            }

    response = product_model.view_product(product_id)
    response["headers"] = {"Content-Type": "application/json"}
    return response

def add_product_inventory_handler(event, context):
    """Handler for adding inventory to a product."""
    body = json.loads(event.get("body", "{}"), parse_float=Decimal)
    product_id = body.get("product_id")
    quantity = body.get("quantity")
    
    if not product_id or quantity is None:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Invalid input: Missing product_id or quantity"})
        }
    
    response = product_model.update_product_quantity(product_id, quantity)
    response["headers"] = {"Content-Type": "application/json"}
    return response

def get_all_product_names_handler(event, context):
    """Handler for retrieving all product names."""
    return product_model.get_all_product_names()
