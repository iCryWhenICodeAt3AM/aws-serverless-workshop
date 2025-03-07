import json
import boto3 #type: ignore
from utils.aws_resources import DecimalEncoder

eventbridge_client = boto3.client("events")

def submit_product_creation_event(product):
    """Submit an event to EventBridge upon product creation."""
    event_detail = {
        "source": "com.rey.products",
        "detail-type": "create_product",
        "detail": json.dumps(product, cls=DecimalEncoder)
    }
    response = eventbridge_client.put_events(
        Entries=[
            {
                "Source": event_detail["source"],
                "DetailType": event_detail["detail-type"],
                "Detail": event_detail["detail"],
                "EventBusName": "custom-rey-event-bus"
            }
        ]
    )
    return response
