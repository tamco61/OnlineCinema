-- Analytics Service ClickHouse Schema

-- Create database
CREATE DATABASE IF NOT EXISTS analytics;

USE analytics;

-- Viewing Events Table
-- Stores all user viewing events (start, progress, finish)
CREATE TABLE IF NOT EXISTS viewing_events (
    id UUID DEFAULT generateUUIDv4(),
    user_id UUID,
    movie_id UUID,
    event_type LowCardinality(String), -- 'start', 'progress', 'finish'
    position_seconds UInt32,
    event_time DateTime,
    session_id Nullable(UUID),
    metadata String, -- JSON metadata
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, user_id, movie_id)
TTL event_time + INTERVAL 365 DAY -- Data retention: 1 year
SETTINGS index_granularity = 8192;

-- Indexes for common queries
-- Index on user_id for user-specific queries
ALTER TABLE viewing_events ADD INDEX idx_user_id (user_id) TYPE bloom_filter GRANULARITY 1;

-- Index on movie_id for content-specific queries
ALTER TABLE viewing_events ADD INDEX idx_movie_id (movie_id) TYPE bloom_filter GRANULARITY 1;

-- Materialized View for Popular Content
-- Pre-aggregates data for faster popular content queries
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
GROUP BY movie_id, event_date;

-- Materialized View for User Stats
-- Pre-aggregates user statistics
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
GROUP BY user_id, event_date;

-- Example Queries:

-- 1. Most popular movies in last 7 days
-- SELECT
--     movie_id,
--     sum(start_count) as total_views,
--     sum(unique_viewers) as total_viewers
-- FROM popular_content_mv
-- WHERE event_date >= today() - 7
-- GROUP BY movie_id
-- ORDER BY total_views DESC
-- LIMIT 10;

-- 2. User viewing statistics
-- SELECT
--     sum(movies_started) as total_started,
--     sum(movies_finished) as total_finished,
--     sum(unique_movies) as unique_movies_watched
-- FROM user_stats_mv
-- WHERE user_id = '{user_id}'
--   AND event_date >= today() - 30;

-- 3. Viewing completion rate by movie
-- SELECT
--     movie_id,
--     countIf(event_type = 'start') as starts,
--     countIf(event_type = 'finish') as finishes,
--     round(finishes / starts * 100, 2) as completion_rate
-- FROM viewing_events
-- WHERE event_time >= now() - INTERVAL 7 DAY
-- GROUP BY movie_id
-- HAVING starts > 10
-- ORDER BY completion_rate DESC;

-- 4. Average watch time per movie
-- SELECT
--     movie_id,
--     avg(position_seconds) as avg_watch_time,
--     max(position_seconds) as max_watch_time
-- FROM viewing_events
-- WHERE event_type = 'finish'
--   AND event_time >= now() - INTERVAL 7 DAY
-- GROUP BY movie_id
-- ORDER BY avg_watch_time DESC;

-- 5. Peak viewing hours
-- SELECT
--     toHour(event_time) as hour,
--     count() as events_count,
--     uniq(user_id) as unique_users
-- FROM viewing_events
-- WHERE event_time >= now() - INTERVAL 7 DAY
-- GROUP BY hour
-- ORDER BY hour;
