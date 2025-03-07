import urllib.parse
from utils.aws_resources import aws_resources, logger

def download_file_from_s3(event, folder_prefix):
    """
    Extracts file details from an S3 event, ensures the file is in the correct folder,
    and downloads it to the /tmp directory.
    """
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"])

    if not key.startswith(f"{folder_prefix}/"):
        logger.info(f"File is not in '{folder_prefix}/' folder. Ignoring...")
        return None, None, {"statusCode": 400, "body": "Invalid file location"}

    local_path = f"/tmp/{key.split('/')[-1]}"
    aws_resources.s3_client.download_file(bucket, key, local_path)
    return bucket, local_path, None
