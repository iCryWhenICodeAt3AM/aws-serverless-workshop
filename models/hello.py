import json

def hello(event):
    """Simple test function to verify API is working."""
    print("Event:", json.dumps(event, indent=2))
    return {"statusCode": 200, "body": json.dumps({"message": "Hello! API is working."})}