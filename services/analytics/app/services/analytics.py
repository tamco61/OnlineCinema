from app.services.clickhouse import ClickHouseClient
from app.schemas.analytics import (
    PopularContentItem,
    PopularContentResponse,
    UserStatsResponse
)

import logging

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

        try:
            results = self.ch.execute(query, {'days': days, 'limit': limit})

            items = [
                PopularContentItem(
                    movie_id=str(row[0]),
                    total_views=int(row[1]),
                    unique_viewers=int(row[2]),
                    completion_rate=float(row[3]) if row[3] else None
                )
                for row in results
            ]

            return PopularContentResponse(
                items=items,
                period_days=days,
                total_items=len(items)
            )

        except Exception as e:
            logger.error(f"Error getting popular content: {e}")
            raise

    def get_user_stats(self, user_id: str, days: int = 30) -> UserStatsResponse:
        stats_query = """
        SELECT
            sum(movies_started) as total_started,
            sum(movies_finished) as total_finished,
            sum(unique_movies) as unique_movies
        FROM user_stats_mv
        WHERE user_id = %(user_id)s
          AND event_date >= today() - %(days)s
        """

        watch_time_query = """
        SELECT sum(position_seconds) as total_seconds
        FROM viewing_events
        WHERE user_id = %(user_id)s
          AND event_type = 'finish'
          AND event_time >= now() - INTERVAL %(days)s DAY
        """

        most_watched_query = """
        SELECT movie_id, count() as watch_count
        FROM viewing_events
        WHERE user_id = %(user_id)s
          AND event_type = 'start'
          AND event_time >= now() - INTERVAL %(days)s DAY
        GROUP BY movie_id
        ORDER BY watch_count DESC
        LIMIT 1
        """

        try:
            params = {'user_id': user_id, 'days': days}

            stats_result = self.ch.execute(stats_query, params)
            watch_time_result = self.ch.execute(watch_time_query, params)
            most_watched_result = self.ch.execute(most_watched_query, params)

            if stats_result and stats_result[0]:
                total_started = int(stats_result[0][0] or 0)
                total_finished = int(stats_result[0][1] or 0)
                unique_movies = int(stats_result[0][2] or 0)
            else:
                total_started = 0
                total_finished = 0
                unique_movies = 0

            total_watch_time = int(watch_time_result[0][0] or 0) if watch_time_result else 0

            most_watched_movie = str(most_watched_result[0][0]) if most_watched_result else None

            completion_rate = (total_finished / total_started * 100) if total_started > 0 else 0.0

            return UserStatsResponse(
                user_id=user_id,
                movies_started=total_started,
                movies_finished=total_finished,
                unique_movies_watched=unique_movies,
                total_watch_time_seconds=total_watch_time,
                completion_rate=round(completion_rate, 2),
                period_days=days,
                most_watched_movie_id=most_watched_movie
            )

        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            raise

    def get_viewing_trends(self, days: int = 7) -> dict:
        query = """
        SELECT
            toDate(event_time) as date,
            countIf(event_type = 'start') as starts,
            countIf(event_type = 'finish') as finishes,
            uniq(user_id) as unique_users,
            uniq(movie_id) as unique_movies
        FROM viewing_events
        WHERE event_time >= now() - INTERVAL %(days)s DAY
        GROUP BY date
        ORDER BY date
        """

        try:
            results = self.ch.execute(query, {'days': days})

            trends = [
                {
                    "date": str(row[0]),
                    "starts": int(row[1]),
                    "finishes": int(row[2]),
                    "unique_users": int(row[3]),
                    "unique_movies": int(row[4])
                }
                for row in results
            ]

            return {
                "period_days": days,
                "trends": trends
            }

        except Exception as e:
            logger.error(f"Error getting viewing trends: {e}")
            raise

    def get_peak_hours(self, days: int = 7) -> dict:
        query = """
        SELECT
            toHour(event_time) as hour,
            count() as events_count,
            uniq(user_id) as unique_users
        FROM viewing_events
        WHERE event_time >= now() - INTERVAL %(days)s DAY
        GROUP BY hour
        ORDER BY hour
        """

        try:
            results = self.ch.execute(query, {'days': days})

            hours = [
                {
                    "hour": int(row[0]),
                    "events_count": int(row[1]),
                    "unique_users": int(row[2])
                }
                for row in results
            ]

            return {
                "period_days": days,
                "peak_hours": hours
            }

        except Exception as e:
            logger.error(f"Error getting peak hours: {e}")
            raise
