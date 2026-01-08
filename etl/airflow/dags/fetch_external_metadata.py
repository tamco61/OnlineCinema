import logging
import os
from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

schedule_cron = os.getenv("FETCH_EXTERNAL_METADATA_SCHEDULE_CRON", "0 2 * * *")
is_init_paused = (os.getenv("FETCH_EXTERNAL_METADATA_IS_INIT_PAUSED", "False")).lower() == "true"
default_args = {
    'owner': 'cinema-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'fetch_external_metadata',
    default_args=default_args,
    description='Fetch movie metadata from TMDb and IMDB',
    schedule_interval=schedule_cron,
    is_paused_upon_creation=is_init_paused,
    catchup=False,
    tags=['etl', 'metadata', 'tmdb', 'imdb'],
)


def get_movies_needing_metadata(**context):
    logger.info("Getting movies needing metadata...")

    pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')
    for_update_interval = os.getenv("FETCH_EXTERNAL_METADATA_FOR_UPDATE_INTERVAL", "30 days")

    query = """
    SELECT id, title, year, tmdb_id, imdb_id
    FROM movies
    WHERE
        (tmdb_id IS NULL OR imdb_id IS NULL)
        OR updated_at IS NULL
        OR updated_at < NOW() - (%(interval)s::interval)
    LIMIT 100
    """
    records = pg_hook.get_records(query, parameters={"interval": for_update_interval})

    movies = [
        {
            'id': str(record[0]),
            'title': record[1],
            'year': record[2],
            'tmdb_id': record[3],
            'imdb_id': record[4]
        }
        for record in records
    ]

    logger.info(f"Found {len(movies)} movies needing metadata")
    context['task_instance'].xcom_push(key='movies', value=movies)
    return len(movies)


def fetch_tmdb_metadata(**context):
    logger.info("Fetching metadata from TMDb...")

    movies = context['task_instance'].xcom_pull(
        task_ids='get_movies_needing_metadata',
        key='movies'
    )

    if not movies:
        logger.info("No movies to fetch metadata for")
        return 0

    tmdb_api_key = os.getenv("TMDB_API_KEY")
    base_url = os.getenv("TMDB_BASE_URL")
    image_base_url = os.getenv("TMDB_IMAGE_BASE_URL")

    updated_count = 0
    metadata_list = []

    for movie in movies:
        try:
            search_url = f"{base_url}/search/movie"
            params = {
                'query': movie['title'],
                'year': movie['year'],
                'language': 'en-US'
            }
            headers = {
                'Authorization': f'Bearer {tmdb_api_key}',
                'Accept': 'application/json'
            }

            response = requests.get(search_url, params=params, headers=headers, timeout=10, verify=False)
            response.raise_for_status()

            results = response.json().get('results', [])

            if results:
                tmdb_id = results[0]['id']
                detail_url = f"{base_url}/movie/{tmdb_id}"
                detail_params = {
                    'api_key': tmdb_api_key,
                    'language': 'ru-RU',
                    'append_to_response': 'credits,videos'
                }

                detail_response = requests.get(detail_url, params=detail_params, headers=headers, timeout=10,
                                               verify=False)
                detail_response.raise_for_status()

                detail = detail_response.json()

                metadata = {
                    'movie_id': movie['id'],
                    'tmdb_id': tmdb_id,
                    'imdb_id': detail.get('imdb_id'),
                    'original_title': detail.get('original_title'),
                    'description': detail.get('overview'),
                    'published_at': detail.get('release_date'),
                    'duration': detail.get('runtime'),
                    'rating': detail.get('vote_average'),
                    'genres': [g['name'] for g in detail.get('genres', [])],
                    'poster_path': (image_base_url + detail.get('poster_path')),
                    'actors': [
                        c['name'] for c in detail.get('credits', {}).get('cast', [])[:10]
                    ],
                    'directors': [
                        c['name'] for c in detail.get('credits', {}).get('crew', [])
                        if is_director_in_crew(c)
                    ]
                }

                metadata_list.append(metadata)
                updated_count += 1

                logger.info(f"Fetched metadata for: {movie['title']}")

        except Exception as e:
            logger.error(f"Error fetching metadata for {movie['title']}: {e}")
            raise e

    logger.info(f"Fetched metadata for {updated_count} movies")
    context['task_instance'].xcom_push(key='metadata', value=metadata_list)

    return updated_count


def is_director_in_crew(crew_member):
    job = crew_member['job'].lower()
    return any(keyword in job for keyword in ['director', 'novel', 'producer', 'screenplay', 'writer', 'screenwriter'])


def update_database_with_metadata(**context):
    logger.info("Updating database with metadata...")

    metadata_list = context['task_instance'].xcom_pull(
        task_ids='fetch_tmdb_metadata',
        key='metadata'
    )

    if not metadata_list:
        logger.info("No metadata to update")
        return 0

    pg_hook = PostgresHook(postgres_conn_id='catalog_postgres')

    updated_count = 0

    for metadata in metadata_list:
        try:
            update_query = """
            UPDATE movies
            SET
                tmdb_id = %(tmdb_id)s,
                imdb_id = %(imdb_id)s,
                original_title = %(original_title)s,
                description = COALESCE(%(description)s, description),
                published_at = COALESCE(%(published_at)s, published_at),
                duration = COALESCE(%(duration)s, duration),
                rating = COALESCE(%(rating)s, rating),
                poster_url = CASE
                    WHEN %(poster_path)s IS NOT NULL
                    THEN %(poster_path)s
                    ELSE poster_url
                END,
                updated_at = NOW()
            WHERE id = %(movie_id)s
            """

            pg_hook.run(update_query, parameters=metadata)

            updated_count += 1

        except Exception as e:
            logger.error(f"Error updating movie {metadata['movie_id']}: {e}")
            continue

    logger.info(f"Updated {updated_count} movies in database")

    return updated_count


get_movies_task = PythonOperator(
    task_id='get_movies_needing_metadata',
    python_callable=get_movies_needing_metadata,
    dag=dag,
)

fetch_metadata_task = PythonOperator(
    task_id='fetch_tmdb_metadata',
    python_callable=fetch_tmdb_metadata,
    dag=dag,
)

update_db_task = PythonOperator(
    task_id='update_database_with_metadata',
    python_callable=update_database_with_metadata,
    dag=dag,
)

get_movies_task >> fetch_metadata_task >> update_db_task
