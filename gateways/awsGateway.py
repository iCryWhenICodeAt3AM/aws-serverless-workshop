import os
import boto3

class AWSGateway:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.padeliver_table = self.dynamodb.Table(os.getenv('PADELIVER_PRODUCTS_TABLE'))

    def get_padeliver_products(self):
        try:
            response = self.padeliver_table.scan()
            products = response.get('Items', [])
            return products
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []

    def batch_create_products(self, products):
        try:
            with self.padeliver_table.batch_writer() as batch:
                for product in products:
                    batch.put_item(Item=product)
        except Exception as e:
            print(f"Error batch creating products: {e}")

    def batch_delete_products(self, product_ids):
        try:
            with self.padeliver_table.batch_writer() as batch:
                for product_id in product_ids:
                    batch.delete_item(Key={'product_id': product_id})
        except Exception as e:
            print(f"Error batch deleting products: {e}")

    def get_s3_object(self, bucket_name, key):
        try:
            response = self.s3.get_object(Bucket=bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8').splitlines()
            return content
        except Exception as e:
            print(f"Error fetching S3 object: {e}")
            return None

    def search_padeliver_products_by_id(self, product_id):
        try:
            response = self.padeliver_table.get_item(Key={'product_id': product_id})
            product = response.get('Item', {})
            return [product] if product else []
        except Exception as e:
            print(f"Error searching product by ID: {e}")
            return []

    def search_padeliver_products_by_name(self, product_name):
        try:
            response = self.padeliver_table.scan(
                FilterExpression="contains(item, :name)",
                ExpressionAttributeValues={":name": product_name}
            )
            products = response.get('Items', [])
            return products
        except Exception as e:
            print(f"Error searching product by name: {e}")
            return []
