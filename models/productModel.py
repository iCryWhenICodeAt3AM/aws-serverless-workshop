import json
import csv
from decimal import Decimal
import boto3 #type: ignore
from gateways import dynamodb_gateway, s3_gateway, sqs_gateway
from utils.aws_resources import logger, DecimalEncoder

class ProductModel:
    def __init__(self):
        self.dynamodb_gateway = dynamodb_gateway
        self.s3_gateway = s3_gateway
        self.sqs_gateway = sqs_gateway
        self.logger = logger
        self.cloudwatch_logs = boto3.client('logs')

    def create_product(self, event):
        """Create a product."""
        body = json.loads(event.get("body", "{}"), parse_float=Decimal)
        if not body or "product_id" not in body:
            return {"statusCode": 400, "body": json.dumps({"message": "Invalid input: Missing product_id"})}
        self.logger.info(f"Creating product: {body}")
        self.logger.info(json.dumps({"message": "Product created!"}))
        self.dynamodb_gateway.save_product(body)
        try:
            self.sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Get All Products! Items: {body}")
        except Exception:
            return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        return {"statusCode": 200, "body": json.dumps({"message": "Product created successfully", "product": body}, cls=DecimalEncoder)}

    def get_all_products(self):
        """Retrieve all products."""
        items = self.dynamodb_gateway.scan_products()
        try:
            self.sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Get All Products! Items: {items}")
        except Exception:
            return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        return {"statusCode": 200, "body": json.dumps({"items": items, "status": "success"}, cls=DecimalEncoder)}

    def view_product(self, product_id):
        """Retrieve a single product by ID."""
        if not product_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Missing product_id"})
            }
        item = self.dynamodb_gateway.get_product(product_id)
        if not item:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Product not found"})
            }
        try:
            self.sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Get a Product! {product_id}")
        except Exception:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Error sending message to SQS"})
            }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(item, cls=DecimalEncoder)
        }

    def edit_product(self, data):
        """Edit an existing product."""
        product_id = data.get("product_id")
        if not product_id:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing product_id"})}
        update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in data if k != "product_id")
        expression_values = {f":{k}": v for k, v in data.items() if k != "product_id"}
        self.dynamodb_gateway.update_product(product_id, update_expression, expression_values)
        try:
            self.sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Edited a Product! Item: {product_id}")
        except Exception:
            return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        return {"statusCode": 200, "body": json.dumps({"message": "Product updated successfully"})}

    def delete_product(self, product_id):
        """Delete a product."""
        if not product_id:
            return {"statusCode": 400, "body": json.dumps({"message": "Missing product_id"})}
        self.dynamodb_gateway.delete_product(product_id)
        try:
            self.sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Deleted a Product! Item: {product_id}")
        except Exception:
            return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        return {"statusCode": 200, "body": json.dumps({"message": f"Product {product_id} deleted successfully"})}

    def batch_create_products_model(self, event):
        """Batch create products from an S3 CSV file."""
        self.logger.info("Batch create model triggered.")
        bucket, local_filename, error = self.s3_gateway.download_file_from_s3(event, "for_create")
        if error:
            return error
        with open(local_filename, "r") as f:
            csv_reader = csv.DictReader(f)
            items = list(csv_reader)
        if not items:
            return {"statusCode": 400, "body": json.dumps({"message": "CSV file is empty"})}
        self.dynamodb_gateway.batch_create_products(items)
        self.logger.info(f"Inserted {len(items)} products successfully.")
        try:
            self.sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Batch Create Triggered! Items: {items}")
        except Exception:
            return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        return {"statusCode": 200, "body": json.dumps({"message": f"{len(items)} products created."})}

    def batch_delete_products_model(self, event):
        """Batch delete products from an S3 CSV file."""
        self.logger.info("Batch delete model triggered.")
        bucket, local_filename, error = self.s3_gateway.download_file_from_s3(event, "for_delete")
        if error:
            return error
        with open(local_filename, "r") as f:
            reader = csv.reader(f)
            product_ids = [row[0] for row in reader if row]
        if not product_ids:
            return {"statusCode": 400, "body": json.dumps({"message": "No product IDs found"})}
        self.dynamodb_gateway.batch_delete_products(product_ids)
        self.logger.info(f"Deleted {len(product_ids)} products successfully.")
        try:
            self.sqs_gateway.send_sqs_message("products-queue-rey-sqs", f"Function: Batch delete triggered! Items: {product_ids}")
        except Exception:
            return {"statusCode": 500, "body": json.dumps({"message": "Error sending message to SQS"})}
        return {"statusCode": 200, "body": json.dumps({"message": f"Deleted {len(product_ids)} products"})}

    def update_product_inventory(self, event):
        """Update product inventory based on new inventory records."""
        body = json.loads(event.get("body", "{}"), parse_float=Decimal)
        if not body or "product_id" not in body or "quantity" not in body:
            return {"statusCode": 400, "body": json.dumps({"message": "Invalid input: Missing product_id or quantity"})}
        
        # Save inventory record only if product exists
        self.dynamodb_gateway.save_product_inventory(body)
        
        return {"statusCode": 200, "body": json.dumps({"message": "Product inventory updated successfully"})}
