import json
import boto3 #type: ignore
import logging
import os
from decimal import Decimal

class AWSResources:
    def __init__(self, region_name="us-east-2"):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.sqs = boto3.resource("sqs", region_name=region_name)
        self.products_table = self.dynamodb.Table(os.getenv("PRODUCTS_TABLE"))
        self.product_inventory_table = self.dynamodb.Table(os.getenv("PRODUCTS_INVENTORY_TABLE"))
        self.product_name_table = self.dynamodb.Table(os.getenv("PRODUCT_NAME_TABLE"))

class Logger:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

    def get_logger(self):
        return self.logger

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

aws_resources = AWSResources()
logger = Logger().get_logger()
