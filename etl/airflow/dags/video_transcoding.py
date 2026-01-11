import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

schedule_cron = os.getenv("VIDEO_TRANSCODING_SCHEDULE_CRON", "0 * * * *")
is_init_paused = (os.getenv("VIDEO_TRANSCODING_IS_INIT_PAUSED", False)).lower() == 'true'
default_args = {
    'owner': 'cinema-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'video_transcoding',
    default_args=default_args,
    description='Schedule video transcoding tasks for Celery',
    schedule_interval=schedule_cron,
    is_paused_upon_creation=is_init_paused,
    catchup=False,
    tags=['etl', 'video', 'transcoding', 'celery'],
)


def get_videos_needing_transcoding(**context):
    logger.info("Getting videos needing transcoding...")

    pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')

    query = """
    SELECT
        id,
        movie_id,
        original_file_path,
        s3_key,
        status,
        resolution,
        duration
    FROM videos
    WHERE status = 'uploaded'
        AND transcoding_status IS NULL
    ORDER BY created_at ASC
    LIMIT 10
    """

    records = pg_hook.get_records(query)
    videos = [
        {
            'id': str(record[0]),
            'movie_id': str(record[1]),
            'original_file_path': record[2],
            's3_key': record[3],
            'status': record[4],
            'resolution': record[5],
            'duration': record[6]
        }
        for record in records
    ]

    logger.info(f"Found {len(videos)} videos needing transcoding")
    context['task_instance'].xcom_push(key='videos', value=videos)

    return len(videos)


def schedule_transcoding_tasks(**context):
    logger.info("Scheduling transcoding tasks...")

    videos = context['task_instance'].xcom_pull(
        task_ids='get_videos_needing_transcoding',
        key='videos'
    )

    if not videos:
        logger.info("No videos to transcode")
        return 0

    from celery import Celery

    celery_app = Celery(
        'etl_tasks',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )

    scheduled_count = 0

    for video in videos:
        try:
            task_params = {
                'video_id': video['id'],
                'movie_id': video['movie_id'],
                's3_key': video['s3_key'],
                'original_file_path': video['original_file_path'],
                'output_formats': ['hls', 'dash'],
                'resolutions': ['1080p', '720p', '480p']
            }

            result = celery_app.send_task(
                'tasks.transcoding.transcode_video',
                kwargs=task_params,
                queue='transcoding'
            )

            logger.info(f"Scheduled transcoding for video {video['id']}: {result.id}")

            pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')
            update_query = """
            UPDATE videos
            SET
                transcoding_status = 'scheduled',
                transcoding_task_id = %s,
                updated_at = NOW()
            WHERE id = %s
            """
            pg_hook.run(update_query, parameters=[result.id, video['id']])
            scheduled_count += 1

        except Exception as e:
            logger.error(f"Error scheduling transcoding for video {video['id']}: {e}")
            continue

    logger.info(f"Scheduled {scheduled_count} transcoding tasks")

    return scheduled_count


def schedule_thumbnail_generation(**context):
    logger.info("Scheduling thumbnail generation...")

    videos = context['task_instance'].xcom_pull(
        task_ids='get_videos_needing_transcoding',
        key='videos'
    )

    if not videos:
        logger.info("No videos for thumbnail generation")
        return 0

    from celery import Celery

    celery_app = Celery(
        'etl_tasks',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )

    scheduled_count = 0

    for video in videos:
        try:
            task_params = {
                'video_id': video['id'],
                'movie_id': video['movie_id'],
                's3_key': video['s3_key'],
                'timestamps': [0, 300, 600, 1200, 1800],
                'resolution': '1280x720'
            }

            result = celery_app.send_task(
                'tasks.thumbnails.generate_thumbnails',
                kwargs=task_params,
                queue='thumbnails'
            )

            logger.info(f"Scheduled thumbnail generation for video {video['id']}: {result.id}")

            scheduled_count += 1

        except Exception as e:
            logger.error(f"Error scheduling thumbnails for video {video['id']}: {e}")
            continue

    logger.info(f"Scheduled {scheduled_count} thumbnail tasks")

    return scheduled_count


def monitor_transcoding_progress(**context):
    logger.info("Monitoring transcoding progress...")

    pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')

    query = """
    SELECT
        id,
        transcoding_task_id
    FROM videos
    WHERE transcoding_status IN ('scheduled', 'processing')
    """

    records = pg_hook.get_records(query)

    logger.info(f"Monitoring {len(records)} videos in transcoding")

    from celery import Celery

    celery_app = Celery(
        'etl_tasks',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )

    completed = 0
    failed = 0

    for record in records:
        video_id = str(record[0])
        task_id = record[1]

        try:
            result = celery_app.AsyncResult(task_id)

            if result.ready():
                if result.successful():
                    logger.info(f"Transcoding completed for video {video_id}")
                    completed += 1

                    update_query = """
                    UPDATE videos
                    SET transcoding_status = 'completed',
                        updated_at = NOW()
                    WHERE id = %s
                    """
                    pg_hook.run(update_query, parameters=[video_id])

                else:
                    logger.error(f"Transcoding failed for video {video_id}")
                    failed += 1

                    update_query = """
                    UPDATE videos
                    SET transcoding_status = 'failed',
                        updated_at = NOW()
                    WHERE id = %s
                    """
                    pg_hook.run(update_query, parameters=[video_id])

        except Exception as e:
            logger.error(f"Error checking status for video {video_id}: {e}")
            continue

    logger.info(f"Monitoring complete: {completed} completed, {failed} failed")

    return {'completed': completed, 'failed': failed}


get_videos_task = PythonOperator(
    task_id='get_videos_needing_transcoding',
    python_callable=get_videos_needing_transcoding,
    dag=dag,
)

schedule_transcoding_task = PythonOperator(
    task_id='schedule_transcoding_tasks',
    python_callable=schedule_transcoding_tasks,
    dag=dag,
)

schedule_thumbnails_task = PythonOperator(
    task_id='schedule_thumbnail_generation',
    python_callable=schedule_thumbnail_generation,
    dag=dag,
)

monitor_task = PythonOperator(
    task_id='monitor_transcoding_progress',
    python_callable=monitor_transcoding_progress,
    dag=dag,
)

get_videos_task >> [schedule_transcoding_task, schedule_thumbnails_task]
schedule_transcoding_task >> monitor_task
