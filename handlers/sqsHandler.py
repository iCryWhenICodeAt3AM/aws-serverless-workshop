from gateways import sqs_gateway
from utils.aws_resources import logger
import json

def process_sqs_message(event, context):
    """Lambda function to process SQS messages."""
    queue_name = "products-queue-rey-sqs"
    message_body = sqs_gateway.receive_sqs_message(queue_name)
    if message_body:
        logger.info(f"Processing message: {json.loads(message_body)}")
        # Add your message processing logic here
    else:
        logger.info("No messages to process.")
