#!/bin/bash
set -e

# Create multiple databases for microservices
# This script runs on PostgreSQL container initialization

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create databases for each microservice
    CREATE DATABASE auth_db;
    CREATE DATABASE user_db;
    CREATE DATABASE catalog_db;
    CREATE DATABASE streaming_db;

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE auth_db TO "$POSTGRES_USER";
    GRANT ALL PRIVILEGES ON DATABASE user_db TO "$POSTGRES_USER";
    GRANT ALL PRIVILEGES ON DATABASE catalog_db TO "$POSTGRES_USER";
    GRANT ALL PRIVILEGES ON DATABASE streaming_db TO "$POSTGRES_USER";

    -- Create extensions for each database
    \c auth_db
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    \c user_db
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    \c catalog_db
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    \c streaming_db
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL

echo "Creating videos table..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "catalog_db" \
  -f /docker-entrypoint-initdb.d/001_create_videos_table.sql

echo "All databases created successfully!"
