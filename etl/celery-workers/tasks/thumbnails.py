import logging
import os
import subprocess
from typing import List
from celery_app import app

import boto3
from PIL import Image

logger = logging.getLogger(__name__)

@app.task(name="tasks.thumbnails.generate_thumbnails")
def generate_thumbnails(
        video_id: str,
        movie_id: str,
        s3_key: str,
        timestamps: List[int] = None,
        resolution: str = '1280x720'
) -> dict:
    logger.info(f"Starting thumbnail generation for video {video_id}")

    timestamps = timestamps or [0, 300, 600, 1200, 1800]  # 0s, 5m, 10m, 20m, 30m

    try:
        logger.info("Downloading source video from S3...")
        s3_endpoint_url = os.getenv('AWS_ENDPOINT_URL')
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint_url,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        bucket_name = 'cinema-videos'

        local_video_path = f"/tmp/thumbnails/{video_id}/input.mp4"
        os.makedirs(os.path.dirname(local_video_path), exist_ok=True)

        s3_client.download_file(bucket_name, s3_key, local_video_path)
        logger.info(f"Downloaded: {local_video_path}")

        output_dir = f"/tmp/thumbnails/{video_id}/frames"
        os.makedirs(output_dir, exist_ok=True)

        thumbnail_files = []

        for i, timestamp in enumerate(timestamps):
            output_file = f"{output_dir}/thumbnail_{i:03d}.jpg"

            ffmpeg_cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', local_video_path,
                '-vframes', '1',
                '-s', resolution,
                '-q:v', '2',
                '-y',
                output_file
            ]

            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error at timestamp {timestamp}: {result.stderr}")
                continue

            _optimize_image(output_file)

            thumbnail_files.append({
                'timestamp': timestamp,
                'file_path': output_file,
                'index': i
            })

            logger.info(f"Generated thumbnail at {timestamp}s: {output_file}")

        logger.info("Uploading thumbnails to S3...")

        s3_urls = {}
        for thumb in thumbnail_files:
            filename = os.path.basename(thumb['file_path'])
            s3_thumbnail_key = f"movies/{movie_id}/thumbnails/{video_id}/{filename}"

            s3_client.upload_file(
                thumb['file_path'],
                bucket_name,
                s3_thumbnail_key,
                ExtraArgs={
                    'ContentType': 'image/jpeg',
                    'CacheControl': 'max-age=31536000'  # 1 year
                }
            )

            s3_url = f"https://{os.getenv('S3_ENDPOINT_URL', 'localhost:9000')}/{bucket_name}/{s3_thumbnail_key}"

            s3_urls[f"thumbnail_{thumb['index']}"] = {
                'url': s3_url,
                'timestamp': thumb.get('timestamp'),
            }

            logger.info(f"Uploaded: {s3_thumbnail_key}")

        logger.info("Cleaning up local files...")
        import shutil
        shutil.rmtree(f"/tmp/thumbnails/{video_id}")

        logger.info(f"Thumbnail generation completed for video {video_id}")

        return {
            'video_id': video_id,
            'status': 'completed',
            'thumbnails': s3_urls,
            'count': len(thumbnail_files)
        }

    except Exception as e:
        logger.error(f"Thumbnail generation failed for video {video_id}: {e}")
        raise


def _optimize_image(image_path: str):
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            img.save(
                image_path,
                'JPEG',
                quality=85,
                optimize=True,
                progressive=True
            )

        logger.debug(f"Optimized image: {image_path}")

    except Exception as e:
        logger.warning(f"Failed to optimize image {image_path}: {e}")
