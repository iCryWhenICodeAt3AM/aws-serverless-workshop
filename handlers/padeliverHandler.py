import os
import json
from gateways.awsGateway import AWSGateway
from models.padeliverModel import PadeliverModel

aws_gateway = AWSGateway()
padeliver_model = PadeliverModel()

def get_padeliver_products(event, context):
    products = aws_gateway.get_padeliver_products()
    return {
        'statusCode': 200,
        'body': json.dumps(products),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def process_padeliver_csv(event, context):
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    for record in event['Records']:
        key = record['s3']['object']['key']
        content = aws_gateway.get_s3_object(bucket_name, key)
        if content:
            if key.startswith('for_padeliver_create/'):
                products = padeliver_model.process_create_csv(content)
                aws_gateway.batch_create_products(products)
            elif key.startswith('for_padeliver_delete/'):
                product_ids = padeliver_model.process_delete_csv(content)
                aws_gateway.batch_delete_products(product_ids)
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'CSV processed successfully'}),
        'headers': {
            'Content-Type': 'application/json',
        },
    }
