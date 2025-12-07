#!/bin/bash

# ============================================
# Environment Switcher Script (Linux/MacOS)
# Usage: ./switch-env.sh [local|remote]
# ============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if argument is provided
if [ -z "$1" ]; then
    echo ""
    echo "Usage: ./switch-env.sh [local|remote]"
    echo ""
    echo "Examples:"
    echo "  ./switch-env.sh local   - Switch to LOCAL development (PostgreSQL + Local Storage)"
    echo "  ./switch-env.sh remote  - Switch to REMOTE (GCP Cloud SQL + GCS Storage)"
    echo ""
    exit 1
fi

TARGET=$1

case $TARGET in
    local|l)
        ENV_TYPE="local"
        SOURCE_FILE=".env.local"
        COMPOSE_FILE="docker-compose.local.yml"
        ;;
    remote|r)
        ENV_TYPE="remote"
        SOURCE_FILE=".env.remote"
        COMPOSE_FILE="docker-compose.cloudsql.yml"
        ;;
    *)
        echo -e "${RED}Error: Invalid option '$1'. Use 'local' or 'remote'.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Switching to ${YELLOW}$ENV_TYPE${BLUE} environment...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}Error: $SOURCE_FILE not found!${NC}"
    echo ""
    echo "Please create $SOURCE_FILE first with proper configuration."
    exit 1
fi

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: $COMPOSE_FILE not found!${NC}"
    exit 1
fi

# Backup current .env if it exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}[*]${NC} Backing up current .env to .env.backup"
    cp .env .env.backup
fi

# Copy selected .env file to .env
echo -e "${YELLOW}[*]${NC} Copying $SOURCE_FILE to .env"
cp "$SOURCE_FILE" .env

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to copy $SOURCE_FILE to .env${NC}"
    exit 1
fi

# Display summary
echo -e "${GREEN}[✓] Successfully switched to $ENV_TYPE environment!${NC}"
echo ""
echo -e "${BLUE}Configuration Details:${NC}"
echo "  Environment: $ENV_TYPE"
echo "  .env file: .env (copy of $SOURCE_FILE)"
echo "  Docker Compose: $COMPOSE_FILE"
echo ""

if [ "$ENV_TYPE" = "local" ]; then
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Update .env with your API keys if needed"
    echo "  2. Run: docker-compose -f $COMPOSE_FILE up -d"
    echo "  3. Access API at http://localhost:8000"
    echo "  4. Access PgAdmin at http://localhost:5050"
    echo "  5. Access API Docs at http://localhost:8000/docs"
else
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Ensure GCP credentials are set up:"
    echo "     - gcloud auth application-default login"
    echo "  2. Update .env with your API keys if needed"
    echo "  3. Run: docker-compose -f $COMPOSE_FILE up -d"
    echo "  4. Access API at http://localhost:8000"
    echo "  5. Access API Docs at http://localhost:8000/docs"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Done!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
