# handlers/productHandler.py
import json
from decimal import Decimal
from models.productModel import (
    create_product,
    get_all_products,
    view_product,
    edit_product,
    delete_product
)

def create_one_product(event, context):
    """Handler for creating a product."""
    return create_product(event)

def get_all_products_handler(event, context):
    """Handler for retrieving all products."""
    return get_all_products()

def product_modification(event, context):
    """
    Handler for product modification.
    Uses query parameters to determine the operation:
      - GET: view (requires product_id)
      - PUT: edit (requires product data in body)
      - DELETE: delete (requires product_id in query)
    """
    params = event.get("queryStringParameters", {}) or {}
    # For simplicity, use an override parameter for HTTP method if needed:
    http_method = params.get("http_method", "").upper() or event.get("requestContext", {}).get("http", {}).get("method", "UNKNOWN")
    if http_method == "GET":
        return view_product(params.get("product_id"))
    elif http_method == "PUT":
        data = json.loads(event.get("body", "{}"), parse_float=Decimal)
        return edit_product(data)
    elif http_method == "DELETE":
        return delete_product(params.get("product_id"))
    else:
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid action or HTTP method"})}
