import os
import json
import base64
import boto3 #type:ignore
from datetime import datetime

s3 = boto3.client('s3')
s3_bucket_name = os.getenv('S3_BUCKET_NAME')

def upload_image(event, context):
    """Handler for uploading an image to S3."""
    body = json.loads(event.get("body", "{}"))
    image_data = body.get("image_data")  # Base64 string
    image_type = body.get("image_type")  # "brand" or "product"
    image_name = body.get("image_name")

    if not image_data or not image_type or not image_name:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing required fields: image_data, image_type, or image_name"})
        }

    # Determine the folder based on image type
    folder = "brand_images/" if image_type == "brand" else "product_images/"
    key = f"{folder}{image_name}.jpg"

    try:
        # Decode base64 image data
        image_binary = base64.b64decode(image_data)

        # Upload to S3
        s3.put_object(
            Bucket=s3_bucket_name,
            Key=key,
            Body=image_binary,
            ContentType="image/jpeg"
        )

        # Generate the S3 URL
        image_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{key}"

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Image uploaded successfully", "image_url": image_url})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error uploading image: {str(e)}"})
        }

def get_brand_images(event, context):
    """Handler for retrieving all brand images from S3."""
    try:
        # List objects in the brand_images/ folder
        response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix="brand_images/")
        images = []

        if "Contents" in response:
            for obj in response["Contents"]:
                images.append(f"https://{s3_bucket_name}.s3.amazonaws.com/{obj['Key']}")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Brand images retrieved successfully", "images": images})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Error retrieving brand images: {str(e)}"})
        }
