from botocore.exceptions import ClientError
from io import BytesIO
from PIL import Image
from urllib.parse import unquote_plus

import base64
import boto3
import os
import json

BUCKET_NAME = os.environ["BUCKET_NAME"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
S3_RULE_PREFIX = os.environ["S3_RULE_PREFIX"]

dynamodb = boto3.resource("dynamodb")
s3 = boto3.resource("s3")


def extractMetadata(event, context):
    # Get object key
    s3_event = event["Records"][0]["s3"]
    key = unquote_plus(s3_event["object"]["key"])

    # Initialize s3 image object
    img_object = s3.Object(BUCKET_NAME, key)
    img_body = img_object.get()["Body"].read()

    # Get image resolution
    with Image.open(BytesIO(img_body)) as image:
        width, height = image.size

    # Store metadata in DynamoDB
    metadata = {
        "s3objectkey": key,
        "size": str(img_object.content_length),
        "contentType": img_object.content_type,
        "width": str(width),
        "height": str(height),
    }
    dynamodb.Table(DYNAMODB_TABLE).put_item(Item=metadata)

    return metadata


def getMetadata(event, context):
    try:
        # Get s3 object key
        s3objectkey = S3_RULE_PREFIX + event["pathParameters"]["s3objectkey"]

        # Get s3 object metadata
        response = dynamodb.Table(DYNAMODB_TABLE).get_item(
            Key={"s3objectkey": s3objectkey}
        )
        metadata = response["Item"]

        return {"statusCode": 200, "body": json.dumps(metadata)}
    except KeyError:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": f"{s3objectkey} not found!"}),
        }


def getImage(event, context):
    try:
        # Get s3 object key
        filename = event["pathParameters"]["s3objectkey"]
        s3objectkey = S3_RULE_PREFIX + filename
        
        # Check if the image is in the temp folder
        if not os.path.isfile("/tmp/" + filename):
            img_object = s3.Object(BUCKET_NAME, s3objectkey)
            img_object.download_file("/tmp/" + filename)

        # Get image        
        with open("/tmp/" + filename, "rb") as file:
            image = base64.b64encode(file.read()).decode("utf-8")

        return {
            "statusCode": 200,
            "body": image,
            "headers": {
                "Content-Type": img_object.content_type,
            },
            "isBase64Encoded": True,
        }
    except ClientError:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": f"{s3objectkey} not found!"}),
        }


def infoImages(event, context):
    # Get dynamodb items
    items = dynamodb.Table(DYNAMODB_TABLE).scan()["Items"]

    # List content types
    content_type_list = [item["contentType"] for item in items]

    # Get the names of the highest and lowest size images and content type count
    info = {
        "highestSizeImage": max(items, key=lambda item: int(item["size"]))[
            "s3objectkey"
        ],
        "lowestSizeImage": min(items, key=lambda item: int(item["size"]))[
            "s3objectkey"
        ],
        "contentTypes": {
            content_type: content_type_list.count(content_type)
            for content_type in set(content_type_list)
        },
    }

    return {"statusCode": 200, "body": json.dumps(info)}
