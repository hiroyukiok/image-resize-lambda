import json
import logging
import os
import urllib.parse
import io

import boto3
from PIL import Image
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

SRC_PREFIX = os.getenv("SRC_PREFIX", "original/")
DST_PREFIX = os.getenv("DST_PREFIX", "resized/")
MAX_WIDTH = 100  # 横幅最大


def lambda_handler(event, context):
    logger.info("Event: %s", json.dumps(event))

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        src_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        # original/ 以外は無視
        if not src_key.startswith(SRC_PREFIX):
            logger.info("Skip: %s", src_key)
            continue

        dst_key = DST_PREFIX + src_key[len(SRC_PREFIX):]

        try:
            # S3 からオリジナル画像を取得
            response = s3.get_object(Bucket=bucket, Key=src_key)
            img_data = response["Body"].read()

            with Image.open(io.BytesIO(img_data)) as img:
                img_format = img.format or "JPEG"  # フォーマットが取れない場合の保険
                w_percent = MAX_WIDTH / float(img.width)
                h_size = int(float(img.height) * w_percent)

                logger.info(f"Resizing {src_key} to width={MAX_WIDTH}, height={h_size}")
                img_resized = img.resize(
                    (MAX_WIDTH, h_size), Image.Resampling.LANCZOS
                )

                # バッファに保存
                buffer = io.BytesIO()
                img_resized.save(buffer, format=img_format)
                buffer.seek(0)

                # S3 にアップロード
                s3.put_object(
                    Bucket=bucket,
                    Key=dst_key,
                    Body=buffer,
                    ContentType=response.get("ContentType", "image/jpeg"),
                )

                logger.info("Resized image saved: s3://%s/%s", bucket, dst_key)

        except ClientError as e:
            logger.error("S3 ClientError: %s", e, exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Failed to process {src_key}"}),
            }

        except Exception as e:
            logger.error("Unexpected error: %s", e, exc_info=True)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)}),
            }

    return {"statusCode": 200, "body": "done"}


