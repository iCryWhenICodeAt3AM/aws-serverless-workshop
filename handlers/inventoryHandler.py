import json
from gateways.awsGateway import AWSGateway
from decimal import Decimal

aws_gateway = AWSGateway()

def decimal_default(obj):
    """Convert Decimal to int or float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def get_all_inventory(event, context):
    """Handler for retrieving all inventory records."""
    try:
        inventory = aws_gateway.get_all_inventory()
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(inventory, default=decimal_default)  # Use custom serializer
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error retrieving inventory: {str(e)}"})
        }
