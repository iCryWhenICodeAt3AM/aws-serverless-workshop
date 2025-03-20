import csv
from io import StringIO

class PadeliverModel:
    def __init__(self):
        pass

    def process_create_csv(self, content):
        """Parse the CSV content for batch creation of products."""
        products = []
        csv_reader = csv.DictReader(StringIO('\n'.join(content)))
        for row in csv_reader:
            product = {
                "product_id": row.get("product_id"),
                "item": row.get("item"),
                "product_description": row.get("product_description"),
                "price": str(row.get("price")),  # Ensure price is stored as a string
                "brand": row.get("brand"),
                "category": row.get("category"),
            }
            if not product["product_id"] or not product["item"]:
                raise ValueError(f"Invalid product data: {row}")
            products.append(product)

        return products

    def process_delete_csv(self, content):
        """Parse the CSV content for batch deletion of products."""
        product_ids = []
        csv_reader = csv.DictReader(StringIO('\n'.join(content)))
        for row in csv_reader:
            product_id = row.get("product_id")
            if not product_id:
                raise ValueError(f"Invalid product ID in row: {row}")
            product_ids.append(product_id)

        return product_ids
