import json
from utils.aws_resources import SQS, DecimalEncoder, logger

def send_sqs_message(queue_name, message_body):
    """Send a message to the specified SQS queue."""
    try:
        queue = SQS.get_queue_by_name(QueueName=queue_name)
        queue.send_message(MessageBody=json.dumps(message_body, cls=DecimalEncoder))
        logger.info(f"Sent SQS message to {queue_name}: {message_body}")
    except Exception as e:
        logger.error(f"Error sending SQS message: {e}")
        raise
