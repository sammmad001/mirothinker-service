#!/usr/bin/env bash
# MiroThinker Service - Start Script
# Starts the application in development or production mode

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "Loaded environment from .env"
else
    echo "Warning: .env file not found, using defaults"
fi

# Default configuration
MODE=${1:-dev}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

case $MODE in
    dev)
        echo "========================================"
        echo "Starting MiroThinker in DEVELOPMENT mode"
        echo "========================================"
        echo "URL: http://localhost:$PORT"
        echo ""
        cd backend && uvicorn src.main:app --reload --host $HOST --port $PORT
        ;;
    prod)
        echo "========================================"
        echo "Starting MiroThinker in PRODUCTION mode"
        echo "========================================"
        echo "URL: http://$HOST:$PORT"
        echo ""
        WORKERS=${WORKERS:-1}
        cd backend && uvicorn src.main:app \
            --host $HOST \
            --port $PORT \
            --workers $WORKERS \
            --log-level info
        ;;
    docker)
        echo "========================================"
        echo "Starting MiroThinker with Docker"
        echo "========================================"
        docker compose up -d --build
        echo "Services started. Check status with: docker compose ps"
        ;;
    *)
        echo "Usage: $0 {dev|prod|docker}"
        echo ""
        echo "  dev    - Start development server with auto-reload"
        echo "  prod   - Start production server"
        echo "  docker - Start with Docker Compose"
        exit 1
        ;;
esac
