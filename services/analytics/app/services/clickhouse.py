from clickhouse_driver import Client
from app.core.config import settings
import logging
from typing import List

logger = logging.getLogger(__name__)


class ClickHouseClient:
    def __init__(self):
        self.client: Client | None = None

    def connect(self):
        try:
            self.client = Client(
                host=settings.CLICKHOUSE_HOST,
                port=settings.CLICKHOUSE_PORT,
                user=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD,
                database=settings.CLICKHOUSE_DATABASE
            )

            result = self.client.execute("SELECT 1")
            logger.info("Connected to ClickHouse")

        except Exception as e:
            logger.error(f"ClickHouse connection error: {e}")
            raise

    def ensure_database(self):
        try:
            temp_client = Client(
                host=settings.CLICKHOUSE_HOST,
                port=settings.CLICKHOUSE_PORT,
                user=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD
            )

            temp_client.execute(
                f"CREATE DATABASE IF NOT EXISTS {settings.CLICKHOUSE_DATABASE}"
            )

            logger.info(f"Database '{settings.CLICKHOUSE_DATABASE}' ready")

        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise

    def ensure_tables(self):
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS viewing_events (
                id UUID DEFAULT generateUUIDv4(),
                user_id UUID,
                movie_id UUID,
                event_type LowCardinality(String),
                position_seconds UInt32,
                event_time DateTime,
                session_id Nullable(UUID),
                metadata String,
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(event_time)
            ORDER BY (event_time, user_id, movie_id)
            TTL event_time + INTERVAL 365 DAY
            """

            self.client.execute(create_table_sql)
            logger.info("Table 'viewing_events' ready")

            create_mv_popular_sql = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS popular_content_mv
            ENGINE = SummingMergeTree()
            PARTITION BY toYYYYMM(event_date)
            ORDER BY (movie_id, event_date)
            AS SELECT
                movie_id,
                toDate(event_time) as event_date,
                countIf(event_type = 'start') as start_count,
                countIf(event_type = 'finish') as finish_count,
                count() as total_events,
                uniq(user_id) as unique_viewers
            FROM viewing_events
            GROUP BY movie_id, event_date
            """

            self.client.execute(create_mv_popular_sql)
            logger.info("Materialized view 'popular_content_mv' ready")

            create_mv_user_sql = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS user_stats_mv
            ENGINE = SummingMergeTree()
            PARTITION BY toYYYYMM(event_date)
            ORDER BY (user_id, event_date)
            AS SELECT
                user_id,
                toDate(event_time) as event_date,
                countIf(event_type = 'start') as movies_started,
                countIf(event_type = 'finish') as movies_finished,
                count() as total_events,
                uniq(movie_id) as unique_movies
            FROM viewing_events
            GROUP BY user_id, event_date
            """

            self.client.execute(create_mv_user_sql)
            logger.info("Materialized view 'user_stats_mv' ready")

        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def execute(self, query: str, params: dict = None) -> List[tuple]:
        if not self.client:
            raise RuntimeError("ClickHouse client not initialized. Call connect() first.")

        try:
            if params:
                return self.client.execute(query, params)
            return self.client.execute(query)

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise

    def insert(self, table: str, data: List[tuple], columns: List[str] = None):
        if not self.client:
            raise RuntimeError("ClickHouse client not initialized. Call connect() first.")

        try:
            if columns:
                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES"
            else:
                query = f"INSERT INTO {table} VALUES"

            self.client.execute(query, data)
            logger.debug(f"Inserted {len(data)} rows into {table}")

        except Exception as e:
            logger.error(f"Insert error: {e}")
            raise

    def insert_viewing_event(
        self,
        user_id: str,
        movie_id: str,
        event_type: str,
        position_seconds: int,
        event_time: str,
        session_id: str = None,
        metadata: str = "{}"
    ):
        query = """
        INSERT INTO viewing_events
        (user_id, movie_id, event_type, position_seconds, event_time, session_id, metadata)
        VALUES
        """

        data = [(
            user_id,
            movie_id,
            event_type,
            position_seconds,
            event_time,
            session_id,
            metadata
        )]

        self.client.execute(query, data)
        logger.debug(f"Inserted viewing event: {event_type} for user={user_id}, movie={movie_id}")

    def close(self):
        if self.client:
            self.client.disconnect()
            logger.info("🔌 ClickHouse connection closed")


clickhouse = ClickHouseClient()


def get_clickhouse_client() -> ClickHouseClient:
    return clickhouse
