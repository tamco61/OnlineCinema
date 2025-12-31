import logging
import time
from typing import List, Optional

from clickhouse_driver import Client

from shared.utils.telemetry.tracer import trace_span
from shared.utils.telemetry.metrics import counter, histogram

from services.analytics.app.core.config import settings

logger = logging.getLogger(__name__)


class ClickHouseClient:
    def __init__(self):
        self.client: Optional[Client] = None

    def connect(self):
        start_time = time.monotonic()
        try:
            with trace_span("clickhouse.connect"):
                self.client = Client(
                    host=settings.CLICKHOUSE_HOST,
                    port=settings.CLICKHOUSE_PORT,
                    user=settings.CLICKHOUSE_USER,
                    password=settings.CLICKHOUSE_PASSWORD,
                    database=settings.CLICKHOUSE_DATABASE,
                )
                self.client.execute("SELECT 1")
                logger.info("Connected to ClickHouse")

        except Exception as e:
            counter("db_query_errors_total").add(
                1,
                attributes={"db.system": "clickhouse", "operation": "connect"},
            )
            logger.error(f"ClickHouse connection error: {e}")
            raise

        finally:
            histogram("db_query_duration_seconds").record(
                time.monotonic() - start_time,
                attributes={"db.system": "clickhouse", "operation": "connect"},
            )

    def ensure_database(self):
        start_time = time.monotonic()
        try:
            with trace_span("clickhouse.ensure_database"):
                temp_client = Client(
                    host=settings.CLICKHOUSE_HOST,
                    port=settings.CLICKHOUSE_PORT,
                    user=settings.CLICKHOUSE_USER,
                    password=settings.CLICKHOUSE_PASSWORD,
                )
                temp_client.execute(
                    f"CREATE DATABASE IF NOT EXISTS {settings.CLICKHOUSE_DATABASE}"
                )
                logger.info(f"Database '{settings.CLICKHOUSE_DATABASE}' ready")

        except Exception as e:
            counter("db_query_errors_total").add(
                1,
                attributes={"db.system": "clickhouse", "operation": "ensure_database"},
            )
            logger.error(f"Error creating database: {e}")
            raise

        finally:
            histogram("db_query_duration_seconds").record(
                time.monotonic() - start_time,
                attributes={"db.system": "clickhouse", "operation": "ensure_database"},
            )

    def ensure_tables(self):
        start_time = time.monotonic()
        try:
            with trace_span("clickhouse.ensure_tables"):
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
            counter("db_query_errors_total").add(
                1,
                attributes={"db.system": "clickhouse", "operation": "ensure_tables"},
            )
            logger.error(f"Error creating tables: {e}")
            raise

        finally:
            histogram("db_query_duration_seconds").record(
                time.monotonic() - start_time,
                attributes={"db.system": "clickhouse", "operation": "ensure_tables"},
            )

    def execute(self, query: str, params: Optional[dict] = None):
        if not self.client:
            raise RuntimeError("ClickHouse client not initialized. Call connect() first.")

        start_time = time.monotonic()
        try:
            with trace_span("clickhouse.execute", {"db.statement": query}):
                counter("db_queries_total").add(
                    1,
                    attributes={"db.system": "clickhouse", "operation": "execute"},
                )
                return self.client.execute(query, params) if params else self.client.execute(query)

        except Exception as e:
            counter("db_query_errors_total").add(
                1,
                attributes={"db.system": "clickhouse", "operation": "execute"},
            )
            logger.error(f"Query execution error: {e}")
            raise

        finally:
            histogram("db_query_duration_seconds").record(
                time.monotonic() - start_time,
                attributes={"db.system": "clickhouse", "operation": "execute"},
            )

    def insert(self, table: str, data: List[tuple], columns: Optional[List[str]] = None):
        if not self.client:
            raise RuntimeError("ClickHouse client not initialized. Call connect() first.")

        start_time = time.monotonic()
        try:
            with trace_span("clickhouse.insert", {"db.sql.table": table}):
                counter("db_queries_total").add(
                    1,
                    attributes={"db.system": "clickhouse", "operation": "insert"},
                )
                query = (
                    f"INSERT INTO {table} ({', '.join(columns)}) VALUES"
                    if columns else
                    f"INSERT INTO {table} VALUES"
                )
                self.client.execute(query, data)
                logger.debug(f"Inserted {len(data)} rows into {table}")

        except Exception as e:
            counter("db_query_errors_total").add(
                1,
                attributes={"db.system": "clickhouse", "operation": "insert"},
            )
            logger.error(f"Insert error: {e}")
            raise

        finally:
            histogram("db_query_duration_seconds").record(
                time.monotonic() - start_time,
                attributes={"db.system": "clickhouse", "operation": "insert"},
            )

    def insert_viewing_event(
        self,
        user_id: str,
        movie_id: str,
        event_type: str,
        position_seconds: int,
        event_time: str,
        session_id: Optional[str] = None,
        metadata: str = "{}",
    ):
        query = """
        INSERT INTO viewing_events
        (user_id, movie_id, event_type, position_seconds, event_time, session_id, metadata)
        VALUES
        """
        data = [
            (user_id, movie_id, event_type, position_seconds, event_time, session_id, metadata)
        ]

        start_time = time.monotonic()
        try:
            with trace_span(
                "clickhouse.insert_viewing_event",
                {"user.id": user_id, "movie.id": movie_id},
            ):
                counter("db_queries_total").add(
                    1,
                    attributes={
                        "db.system": "clickhouse",
                        "operation": "insert_viewing_event",
                    },
                )
                self.client.execute(query, data)
                logger.debug(
                    f"Inserted viewing event: {event_type} for user={user_id}, movie={movie_id}"
                )

        except Exception as e:
            counter("db_query_errors_total").add(
                1,
                attributes={
                    "db.system": "clickhouse",
                    "operation": "insert_viewing_event",
                },
            )
            logger.error(f"Error inserting viewing event: {e}")
            raise

        finally:
            histogram("db_query_duration_seconds").record(
                time.monotonic() - start_time,
                attributes={
                    "db.system": "clickhouse",
                    "operation": "insert_viewing_event",
                },
            )

    def close(self):
        if self.client:
            self.client.disconnect()
            logger.info("ClickHouse connection closed")


# Singleton клиент
clickhouse = ClickHouseClient()


def get_clickhouse_client() -> ClickHouseClient:
    return clickhouse
