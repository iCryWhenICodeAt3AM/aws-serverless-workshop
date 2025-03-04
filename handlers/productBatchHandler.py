# handlers/productBatchHandler.py
from models.productModel import batch_create_products_model, batch_delete_products_model

def batch_create_products_handler(event, context):
    """Handler for batch creating products via S3 CSV upload."""
    return batch_create_products_model(event)

def batch_delete_products_handler(event, context):
    """Handler for batch deleting products via S3 CSV upload."""
    return batch_delete_products_model(event)
