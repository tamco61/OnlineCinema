import logging
import os
import subprocess
from typing import List, Dict
from celery_app import app

import boto3

logger = logging.getLogger(__name__)

@app.task(name="tasks.transcoding.transcode_video")
def transcode_video(
        video_id: str,
        movie_id: str,
        s3_key: str,
        original_file_path: str,
        output_formats: List[str] = None,
        resolutions: List[str] = None
) -> Dict:
    logger.info(f"Starting transcoding for video {video_id}")

    output_formats = output_formats or ['hls']
    resolutions = resolutions or ['1080p', '720p', '480p']

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

        local_input_path = f"/tmp/videos/{video_id}/input.mp4"
        os.makedirs(os.path.dirname(local_input_path), exist_ok=True)

        s3_client.download_file(bucket_name, s3_key, local_input_path)
        logger.info(f"Downloaded: {local_input_path}")

        output_dir = f"/tmp/videos/{video_id}/output"
        os.makedirs(output_dir, exist_ok=True)

        transcoded_files = {}
        resolution_map = {
            '1080p': {'height': 1080, 'bitrate': '5000k'},
            '720p': {'height': 720, 'bitrate': '2500k'},
            '480p': {'height': 480, 'bitrate': '1000k'},
        }

        for resolution in resolutions:
            logger.info(f"Transcoding to {resolution}...")

            res_config = resolution_map[resolution]
            output_file = f"{output_dir}/{resolution}.mp4"

            ffmpeg_cmd = [
                'ffmpeg',
                '-i', local_input_path,
                '-c:v', 'libx264',  # H.264 codec
                '-preset', 'medium',
                '-crf', '23',
                '-vf', f"scale=-2:{res_config['height']}",
                '-b:v', res_config['bitrate'],
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-y',
                output_file
            ]

            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"Transcoding failed for {resolution}")

            transcoded_files[resolution] = output_file
            logger.info(f"Transcoded {resolution}: {output_file}")

        if 'hls' in output_formats:
            logger.info("Generating HLS manifests...")

            hls_dir = f"{output_dir}/hls"
            os.makedirs(hls_dir, exist_ok=True)

            _generate_hls_master_playlist(
                transcoded_files,
                hls_dir
            )

        if 'dash' in output_formats:
            logger.info("Generating DASH manifests...")

            dash_dir = f"{output_dir}/dash"
            os.makedirs(dash_dir, exist_ok=True)

            _generate_dash_manifest(
                transcoded_files,
                dash_dir
            )

        logger.info("Uploading transcoded files to S3...")

        s3_output_keys = {}

        for resolution, file_path in transcoded_files.items():
            s3_output_key = f"movies/{movie_id}/videos/{video_id}/{resolution}/{os.path.basename(file_path)}"

            s3_client.upload_file(
                file_path,
                bucket_name,
                s3_output_key,
                ExtraArgs={'ContentType': _get_content_type(file_path)}
            )

            s3_output_keys[resolution] = s3_output_key
            logger.info(f"Uploaded: {s3_output_key}")

        logger.info("Cleaning up local files...")
        import shutil
        shutil.rmtree(f"/tmp/videos/{video_id}")

        logger.info(f"Transcoding completed for video {video_id}")

        return {
            'video_id': video_id,
            'status': 'completed',
            'output_files': s3_output_keys,
            'resolutions': list(resolutions),
            'formats': list(output_formats)
        }

    except Exception as e:
        logger.error(f"Transcoding failed for video {video_id}: {e}")
        raise


def _generate_hls_master_playlist(transcoded_files: Dict, output_dir: str) -> str:
    for resolution, mp4_file in transcoded_files.items():
        if resolution.endswith('p'):
            segment_dir = f"{output_dir}/{resolution}"
            os.makedirs(segment_dir, exist_ok=True)

            hls_cmd = [
                'ffmpeg',
                '-i', mp4_file,
                '-c', 'copy',
                '-hls_time', '10',  # 10 second segments
                '-hls_list_size', '0',
                '-hls_segment_filename', f"{segment_dir}/segment_%03d.ts",
                '-f', 'hls',
                f"{segment_dir}/playlist.m3u8"
            ]

            subprocess.run(hls_cmd, capture_output=True, check=True)

    master_playlist_path = f"{output_dir}/master.m3u8"

    bandwidth_map = {
        '1080p': 5000000,
        '720p': 2500000,
        '480p': 1000000,
    }

    with open(master_playlist_path, 'w') as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n\n")

        for resolution in sorted(transcoded_files.keys()):
            if resolution.endswith('p'):
                bandwidth = bandwidth_map.get(resolution, 1000000)
                height = int(resolution.replace('p', ''))

                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={int(height * 16 / 9)}x{height}\n")
                f.write(f"{resolution}/playlist.m3u8\n\n")

    logger.info(f"Generated HLS master playlist: {master_playlist_path}")

    return master_playlist_path


def _generate_dash_manifest(transcoded_files: Dict, output_dir: str) -> str:
    manifest_path = f"{output_dir}/manifest.mpd"

    input_files = [f for r, f in transcoded_files.items() if r.endswith('p')]

    if input_files:
        dash_cmd = [
            'ffmpeg',
            '-i', input_files[0],  # First resolution as base
            '-c', 'copy',
            '-f', 'dash',
            manifest_path
        ]

        subprocess.run(dash_cmd, capture_output=True, check=True)

    logger.info(f"Generated DASH manifest: {manifest_path}")

    return manifest_path


def _get_content_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    content_types = {
        '.mp4': 'video/mp4',
        '.m3u8': 'application/x-mpegURL',
        '.ts': 'video/MP2T',
        '.mpd': 'application/dash+xml',
    }

    return content_types.get(ext, 'application/octet-stream')
