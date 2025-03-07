# handlers/productBatchHandler.py
from models.productModel import ProductModel

product_model = ProductModel()

def batch_create_products_handler(event, context):
    """Handler for batch creating products via S3 CSV upload."""
    return product_model.batch_create_products_model(event)

def batch_delete_products_handler(event, context):
    """Handler for batch deleting products via S3 CSV upload."""
    return product_model.batch_delete_products_model(event)
