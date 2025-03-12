import os
import csv

class PadeliverModel:
    def __init__(self):
        self.table_name = os.getenv('PADELIVER_PRODUCTS_TABLE')

    def get_all_products(self):
        # This method can be updated to fetch products from a different source if needed
        pass

    def batch_create_products(self, products):
        # This method can be updated to create products in a different source if needed
        pass

    def batch_delete_products(self, product_ids):
        # This method can be updated to delete products from a different source if needed
        pass

    def process_create_csv(self, content):
        reader = csv.DictReader(content)
        products = []
        for row in reader:
            try:
                product = {
                    'product_id': row['product_id'],
                    'category': row['category'],
                    'brand': row['brand'],
                    'item': row['item'],
                    'product_description': row['product_description'],
                    'price': row['price']
                }
                products.append(product)
            except ValueError as e:
                print(f"Error processing row {row}: {e}")
        return products

    def process_delete_csv(self, content):
        reader = csv.DictReader(content)
        product_ids = [row['product_id'] for row in reader]
        return product_ids
