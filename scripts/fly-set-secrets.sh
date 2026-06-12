#!/bin/bash
# Set Fly.io secrets for the backend from the local .env file.
# Usage: ./scripts/fly-set-secrets.sh   (run from repo root, after `fly auth login`)
#
# Reads .env and pushes only the runtime secrets Fly needs. PORT lives in
# fly.toml [env], not here. No CLOUD_SQL_INSTANCES => entrypoint skips the proxy.
set -euo pipefail

cd "$(dirname "$0")/.."
[ -f .env ] || { echo "ERROR: .env not found"; exit 1; }

set -a; source .env; set +a

fly secrets set \
  DATABASE_URL="$DATABASE_URL" \
  SECRET_KEY="$SECRET_KEY" \
  ALGORITHM="${ALGORITHM:-HS256}" \
  ACCESS_TOKEN_EXPIRE_MINUTES="${ACCESS_TOKEN_EXPIRE_MINUTES:-1440}" \
  STORAGE_TYPE="${STORAGE_TYPE:-supabase}" \
  SUPABASE_URL="$SUPABASE_URL" \
  SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
  SUPABASE_STORAGE_BUCKET="${SUPABASE_STORAGE_BUCKET:-documents}" \
  OPENAI_API_KEY="$OPENAI_API_KEY" \
  OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
  GOOGLE_API_KEY="${GOOGLE_API_KEY:-}" \
  OPENAI_EMBEDDING_MODEL="${OPENAI_EMBEDDING_MODEL:-text-embedding-3-small}" \
  BACKEND_CORS_ORIGINS="$BACKEND_CORS_ORIGINS" \
  DEBUG="${DEBUG:-false}"

echo "✅ Secrets pushed to Fly app."
