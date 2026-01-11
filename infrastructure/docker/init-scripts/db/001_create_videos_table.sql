CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    movie_id UUID NOT NULL,
    original_file_path TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    resolution TEXT,
    duration INTEGER,
    transcoding_status TEXT,
    transcoding_task_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
