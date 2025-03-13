import os
import boto3
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

class AWSGateway:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.s3 = boto3.client('s3')
        self.padeliver_table = self.dynamodb.Table(os.getenv('PADELIVER_PRODUCTS_TABLE'))
        self.inventory_table = self.dynamodb.Table(os.getenv('PRODUCTS_INVENTORY_TABLE'))

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

    def get_product_names(self):
        """Retrieves all product names."""
        try:
            response = self.padeliver_table.scan()
            products = response.get('Items', [])
            return [{"id": p["product_id"], "name": p["item"]} for p in products]
        except Exception as e:
            print(f"❌ Error fetching product names: {e}")
            return []

    def get_product_name(self, item):
        """Fetches product details by item name WITHOUT using a GSI."""
        try:
            response = self.padeliver_table.scan(
                FilterExpression=Attr('item').eq(item)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            print(f"❌ Error fetching item: {e}")
            return None

    def view_product(self, product_id):
        """Fetches product details by product_id and its inventory if available."""
        if not product_id:
            return {"statusCode": 400, "body": json.dumps({"message": "Invalid product_id"})}

        try:
            response = self.padeliver_table.get_item(Key={'product_id': product_id})
            if 'Item' in response:
                product = response['Item']
                inventory_response = self.inventory_table.query(
                    KeyConditionExpression=Key('product_id').eq(product_id)
                )
                items = inventory_response.get("Items", [])
                total_quantity = sum(Decimal(item['quantity']) for item in items) if items else Decimal(0)
                product['total_quantity'] = total_quantity # Convert Decimal to float
                return {"statusCode": 200, "body": json.dumps(product, default=self.decimal_default)}
            else:
                return {"statusCode": 404, "body": json.dumps({"message": "Product not found"})}
        except Exception as e:
            print(f"❌ Error fetching product: {e}")
            return {"statusCode": 500, "body": json.dumps({"message": f"Error fetching product: {str(e)}"})}

    def decimal_default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError

    def add_inventory_item(self, inventory_item):
        """Adds an inventory item to the inventory table."""
        try:
            self.inventory_table.put_item(Item=inventory_item)
        except Exception as e:
            print(f"❌ Error adding inventory item: {e}")
            raise

    def product_exists(self, product_id):
        """Checks if a product exists in the padeliver table."""
        try:
            response = self.padeliver_table.get_item(Key={'product_id': product_id})
            return 'Item' in response
        except Exception as e:
            print(f"❌ Error checking if product exists: {e}")
            return False
