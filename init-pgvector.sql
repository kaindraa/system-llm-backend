-- PostgreSQL pgvector extension initialization script
-- This script is executed automatically when the PostgreSQL container starts
-- It creates the pgvector extension for vector similarity search (used for RAG/embeddings)

CREATE EXTENSION IF NOT EXISTS pgvector;

-- Vector type for AI embeddings (1536 dimensions for OpenAI embeddings)
-- This allows storing and searching through document embeddings
SELECT 1 as init_complete;
