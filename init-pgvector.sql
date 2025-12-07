-- Initialize pgvector extension for vector embeddings
-- This script runs automatically when PostgreSQL container starts

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- Verify extensions are installed
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp');
