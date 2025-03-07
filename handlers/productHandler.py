import json
from decimal import Decimal
from models.productModel import ProductModel
from utils.event_bridge import submit_product_creation_event

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
