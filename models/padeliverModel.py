import csv

class PadeliverModel:
    def __init__(self):
        pass

    def process_create_csv(self, content):
        """Processes CSV file content and extracts product details."""
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
                print(f"❌ Error processing row {row}: {e}")
        return products

    def process_delete_csv(self, content):
        """Extracts product IDs for deletion from CSV."""
        reader = csv.DictReader(content)
        return [row['product_id'] for row in reader]
