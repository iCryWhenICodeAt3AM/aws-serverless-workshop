import json
import boto3 #type: ignore
import logging
from decimal import Decimal

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS resources
DYNAMODB = boto3.resource("dynamodb", region_name="us-east-2")
S3_CLIENT = boto3.client("s3", region_name="us-east-2")
SQS = boto3.resource("sqs", region_name="us-east-2")

# Define DynamoDB table
PRODUCTS_TABLE_NAME = "products_rey"
PRODUCTS_TABLE = DYNAMODB.Table(PRODUCTS_TABLE_NAME)

# Custom JSON encoder to handle Decimal values
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)
