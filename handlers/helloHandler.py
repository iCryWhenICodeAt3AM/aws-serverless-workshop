import json
from models.hello import hello

def hello_handler(event, context):
    """Handler for simple hello function."""
    return hello(event)