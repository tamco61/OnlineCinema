import time

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from services.streaming.app.core.config import settings
import logging

from shared.utils.telemetry.metrics import counter, histogram

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self):
        self.client = None

    def connect(self):
        start_time = time.monotonic()
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version='s3v4')
            )
            counter("s3_requests_total").add(1, {"operation": "connect"})
            logger.info("Connected to S3/MinIO")
        except Exception as e:
            counter("s3_request_errors_total").add(1, {"operation": "connect"})
            logger.error(f"S3 connection error: {e}")
            raise
        finally:
            histogram("s3_request_duration_seconds").record(time.monotonic() - start_time, {"operation": "connect"})

    def generate_signed_url(self, object_key: str, expiration: int = None) -> str:
        start_time = time.monotonic()
        try:
            if not self.client:
                raise RuntimeError("S3 client not initialized. Call connect() first.")

            expiration = expiration or settings.SIGNED_URL_EXPIRATION

            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )

            counter("s3_requests_total").add(1, {"operation": "generate_signed_url"})
            logger.debug(f"Generated signed URL for: {object_key}")
            return url

        except ClientError as e:
            counter("s3_request_errors_total").add(1, {"operation": "generate_signed_url"})
            logger.error(f"Error generating signed URL for {object_key}: {e}")
            raise
        finally:
            histogram("s3_request_duration_seconds").record(time.monotonic() - start_time, {"operation": "generate_signed_url"})

    def check_object_exists(self, object_key: str) -> bool:
        start_time = time.monotonic()
        try:
            if not self.client:
                raise RuntimeError("S3 client not initialized. Call connect() first.")

            self.client.head_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=object_key
            )

            counter("s3_requests_total").add(1, {"operation": "check_object_exists"})
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                counter("s3_requests_total").add(1, {"operation": "check_object_exists"})
                return False

            counter("s3_request_errors_total").add(1, {"operation": "check_object_exists"})
            raise
        finally:
            histogram("s3_request_duration_seconds").record(time.monotonic() - start_time, {"operation": "check_object_exists"})

    def get_manifest_url(self, movie_id: str, manifest_type: str = "hls") -> str:
        if manifest_type == "hls":
            manifest_file = "index.m3u8"
        elif manifest_type == "dash":
            manifest_file = "index.mpd"
        else:
            raise ValueError(f"Unsupported manifest type: {manifest_type}")

        object_key = f"movies/{movie_id}/{manifest_file}"

        if not self.check_object_exists(object_key):
            raise FileNotFoundError(f"Manifest not found: {object_key}")

        return self.generate_signed_url(object_key)

    def get_segment_url(self, movie_id: str, segment_name: str) -> str:
        object_key = f"movies/{movie_id}/{segment_name}"

        if not self.check_object_exists(object_key):
            raise FileNotFoundError(f"Segment not found: {object_key}")

        return self.generate_signed_url(object_key)


s3_client = S3Client()


def get_s3_client() -> S3Client:
    return s3_client
