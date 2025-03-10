import json
from utils.aws_resources import aws_resources, DecimalEncoder, logger

def send_sqs_message(queue_name, message_body):
    """Send a message to the specified SQS queue."""
    try:
        queue = aws_resources.sqs.get_queue_by_name(QueueName=queue_name)
        queue.send_message(MessageBody=json.dumps(message_body, cls=DecimalEncoder))
        logger.info(f"Sent SQS message to {queue_name}: {message_body}")
    except Exception as e:
        logger.error(f"Error sending SQS message: {e}")
        raise

def receive_sqs_message(queue_name):
    """Receive a message from the specified SQS queue and delete it."""
    try:
        queue = aws_resources.sqs.get_queue_by_name(QueueName=queue_name)
        messages = queue.receive_messages(MaxNumberOfMessages=1)
        if messages:
            message = messages[0]
            logger.info(f"Received SQS message from {queue_name}: {message.body}")
            message.delete()
            logger.info(f"Deleted SQS message from {queue_name}: {message.body}")
            return message.body
        else:
            logger.info(f"No messages available in {queue_name}")
            return None
    except Exception as e:
        logger.error(f"Error receiving SQS message: {e}")
        raise
