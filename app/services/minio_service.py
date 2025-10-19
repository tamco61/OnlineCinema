from minio import Minio
from app.config import settings
from datetime import timedelta

client = Minio(
    endpoint=settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=False
)

def upload_file(file, object_name: str):
    client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=object_name,
        data=file.file,
        length=-1,
        part_size=10*1024*1024
    )

def get_presigned_url(object_name: str, expires=3600):
    return client.presigned_get_object(settings.MINIO_BUCKET, object_name, expires)
