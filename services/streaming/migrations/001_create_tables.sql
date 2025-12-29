-- Streaming Service Database Migration

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Watch Progress
CREATE TABLE watch_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    movie_id UUID NOT NULL,
    position_seconds INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_watched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

CREATE INDEX idx_watch_progress_user_id ON watch_progress(user_id);
CREATE INDEX idx_watch_progress_movie_id ON watch_progress(movie_id);
CREATE INDEX idx_watch_progress_last_watched ON watch_progress(last_watched_at);

-- Stream Sessions
CREATE TABLE stream_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    movie_id UUID NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    user_agent VARCHAR(500),
    ip_address VARCHAR(50)
);

CREATE INDEX idx_stream_sessions_user_id ON stream_sessions(user_id);
CREATE INDEX idx_stream_sessions_movie_id ON stream_sessions(movie_id);
CREATE INDEX idx_stream_sessions_started_at ON stream_sessions(started_at);
