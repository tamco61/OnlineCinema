import logging
import time
from typing import Dict

from services.analytics.app.services.clickhouse import ClickHouseClient
from services.analytics.app.schemas.analytics import (
    PopularContentItem,
    PopularContentResponse,
    UserStatsResponse,
)

from shared.utils.telemetry.tracer import trace_span
from shared.utils.telemetry.metrics import counter, histogram

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, ch_client: ClickHouseClient):
        self.ch = ch_client

    def get_popular_content(self, days: int = 7, limit: int = 10) -> PopularContentResponse:
        query = """
        SELECT
            movie_id,
            sum(start_count) as total_views,
            sum(unique_viewers) as unique_viewers,
            round(sum(finish_count) / sum(start_count) * 100, 2) as completion_rate
        FROM popular_content_mv
        WHERE event_date >= today() - %(days)s
        GROUP BY movie_id
        ORDER BY total_views DESC
        LIMIT %(limit)s
        """

        start_time = time.monotonic()
        try:
            with trace_span("analytics.get_popular_content", {"days": days, "limit": limit}):
                counter("clickhouse_queries_total").add(
                    1, {"operation": "get_popular_content"}
                )

                results = self.ch.execute(query, {"days": days, "limit": limit})

                items = [
                    PopularContentItem(
                        movie_id=str(row[0]),
                        total_views=int(row[1]),
                        unique_viewers=int(row[2]),
                        completion_rate=float(row[3]) if row[3] else None,
                    )
                    for row in results
                ]

                return PopularContentResponse(
                    items=items,
                    period_days=days,
                    total_items=len(items),
                )

        except Exception as e:
            counter("clickhouse_query_errors_total").add(
                1, {"operation": "get_popular_content"}
            )
            logger.error(f"Error getting popular content: {e}")
            raise
        finally:
            histogram("clickhouse_query_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "get_popular_content"},
            )

    def get_user_stats(self, user_id: str, days: int = 30) -> UserStatsResponse:
        stats_query = """
        SELECT sum(movies_started),
               sum(movies_finished),
               sum(unique_movies)
        FROM user_stats_mv
        WHERE user_id = %(user_id)s
          AND event_date >= today() - %(days)s
        """

        watch_time_query = """
        SELECT sum(position_seconds)
        FROM viewing_events
        WHERE user_id = %(user_id)s
          AND event_type = 'finish'
          AND event_time >= now() - INTERVAL %(days)s DAY
        """

        most_watched_query = """
        SELECT movie_id, count()
        FROM viewing_events
        WHERE user_id = %(user_id)s
          AND event_type = 'start'
          AND event_time >= now() - INTERVAL %(days)s DAY
        GROUP BY movie_id
        ORDER BY count() DESC
        LIMIT 1
        """

        start_time = time.monotonic()
        try:
            with trace_span("analytics.get_user_stats", {"user_id": user_id, "days": days}):
                counter("clickhouse_queries_total").add(
                    1, {"operation": "get_user_stats"}
                )

                params = {"user_id": user_id, "days": days}

                stats = self.ch.execute(stats_query, params)
                watch_time = self.ch.execute(watch_time_query, params)
                most_watched = self.ch.execute(most_watched_query, params)

                total_started = int(stats[0][0] or 0) if stats else 0
                total_finished = int(stats[0][1] or 0) if stats else 0
                unique_movies = int(stats[0][2] or 0) if stats else 0

                total_watch_time = int(watch_time[0][0] or 0) if watch_time else 0
                most_watched_movie = str(most_watched[0][0]) if most_watched else None

                completion_rate = (
                    total_finished / total_started * 100
                    if total_started > 0
                    else 0.0
                )

                return UserStatsResponse(
                    user_id=user_id,
                    movies_started=total_started,
                    movies_finished=total_finished,
                    unique_movies_watched=unique_movies,
                    total_watch_time_seconds=total_watch_time,
                    completion_rate=round(completion_rate, 2),
                    period_days=days,
                    most_watched_movie_id=most_watched_movie,
                )

        except Exception as e:
            counter("clickhouse_query_errors_total").add(
                1, {"operation": "get_user_stats"}
            )
            logger.error(f"Error getting user stats: {e}")
            raise
        finally:
            histogram("clickhouse_query_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "get_user_stats"},
            )

    def get_viewing_trends(self, days: int = 7) -> Dict:
        query = """
        SELECT
            toDate(event_time),
            countIf(event_type = 'start'),
            countIf(event_type = 'finish'),
            uniq(user_id),
            uniq(movie_id)
        FROM viewing_events
        WHERE event_time >= now() - INTERVAL %(days)s DAY
        GROUP BY 1
        ORDER BY 1
        """

        start_time = time.monotonic()
        try:
            with trace_span("analytics.get_viewing_trends", {"days": days}):
                counter("clickhouse_queries_total").add(
                    1, {"operation": "get_viewing_trends"}
                )

                results = self.ch.execute(query, {"days": days})

                return {
                    "period_days": days,
                    "trends": [
                        {
                            "date": str(r[0]),
                            "starts": int(r[1]),
                            "finishes": int(r[2]),
                            "unique_users": int(r[3]),
                            "unique_movies": int(r[4]),
                        }
                        for r in results
                    ],
                }

        except Exception as e:
            counter("clickhouse_query_errors_total").add(
                1, {"operation": "get_viewing_trends"}
            )
            logger.error(f"Error getting viewing trends: {e}")
            raise
        finally:
            histogram("clickhouse_query_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "get_viewing_trends"},
            )

    def get_peak_hours(self, days: int = 7) -> Dict:
        query = """
        SELECT
            toHour(event_time),
            count(),
            uniq(user_id)
        FROM viewing_events
        WHERE event_time >= now() - INTERVAL %(days)s DAY
        GROUP BY 1
        ORDER BY 1
        """

        start_time = time.monotonic()
        try:
            with trace_span("analytics.get_peak_hours", {"days": days}):
                counter("clickhouse_queries_total").add(
                    1, {"operation": "get_peak_hours"}
                )

                results = self.ch.execute(query, {"days": days})

                return {
                    "period_days": days,
                    "peak_hours": [
                        {
                            "hour": int(r[0]),
                            "events_count": int(r[1]),
                            "unique_users": int(r[2]),
                        }
                        for r in results
                    ],
                }

        except Exception as e:
            counter("clickhouse_query_errors_total").add(
                1, {"operation": "get_peak_hours"}
            )
            logger.error(f"Error getting peak hours: {e}")
            raise
        finally:
            histogram("clickhouse_query_duration_seconds").record(
                time.monotonic() - start_time,
                {"operation": "get_peak_hours"},
            )
