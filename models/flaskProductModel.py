import os

class FlaskProductModel:
    def __init__(self):
        self.file_path = os.path.join("static", "assets", "products.txt")

    def read_products_from_file(self):
        """Read products from the products.txt file."""
        products = []
        try:
            with open(self.file_path, "r") as file:
                lines = file.readlines()[1:]  # Skip header line
                for line in lines:
                    product_id, category, brand, item, product_description, price = line.strip().split(",")
                    products.append({
                        "product_id": product_id,
                        "category": category,
                        "brand": brand,
                        "item": item,
                        "product_description": product_description,
                        "price": price
                    })
        except Exception as e:
            print(f"Error reading products from file: {e}")
        return products
