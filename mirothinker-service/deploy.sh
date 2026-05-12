#!/bin/bash
# MiroThinker Online Service - Deployment Script
# Supports both direct deployment and Docker deployment

set -e

echo "========================================="
echo "  MiroThinker Online Service Deployment"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Warning: Some operations may require sudo privileges"
    echo ""
fi

# Detect deployment mode
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "Docker detected. Choose deployment mode:"
    echo "  1) Docker Compose (Recommended)"
    echo "  2) Direct Python Deployment"
    echo ""
    read -p "Select mode [1/2]: " mode
else
    echo "Docker not found. Using direct deployment mode."
    mode="2"
fi

echo ""

if [ "$mode" = "1" ]; then
    # === Docker Compose Deployment ===
    echo "=== Docker Compose Deployment ==="
    echo ""

    # Check for .env file
    if [ ! -f .env ]; then
        echo "Setting up environment file..."
        cp .env.example .env
        echo ""
        echo "Please edit .env with your API keys:"
        echo "  nano .env"
        echo ""
        read -p "Press Enter after configuring .env..."
    fi

    echo "Building and starting services..."
    docker-compose down || true
    docker-compose build --no-cache
    docker-compose up -d

    echo ""
    echo "Waiting for service to start..."
    sleep 5

    # Health check
    echo "Running health check..."
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        echo "✅ Service is running!"
        echo ""
        echo "Access points:"
        echo "  Frontend: http://localhost:8000"
        echo "  API:      http://localhost:8000/api/health"
        echo ""
        echo "Management commands:"
        echo "  View logs:     docker-compose logs -f"
        echo "  Stop service:  docker-compose down"
        echo "  Restart:       docker-compose restart"
    else
        echo "❌ Service failed to start. Check logs:"
        echo "  docker-compose logs"
        exit 1
    fi

else
    # === Direct Python Deployment ===
    echo "=== Direct Python Deployment ==="
    echo ""

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed."
        exit 1
    fi

    echo "Python version: $(python3 --version)"
    echo ""

    # Install dependencies
    echo "Installing dependencies..."
    cd backend
    pip3 install -r requirements.txt --quiet

    # Setup environment
    if [ ! -f ../.env ]; then
        echo ""
        echo "Setting up environment file..."
        cp ../.env.example ../.env
        echo ""
        echo "Please edit .env with your API keys:"
        echo "  nano ../.env"
        echo ""
        read -p "Press Enter after configuring .env..."
    fi

    # Load environment variables
    set -a
    source ../.env
    set +a

    # Stop existing process
    echo "Stopping existing service (if any)..."
    pkill -f "uvicorn main:app" 2>/dev/null || true
    sleep 2

    # Start service
    echo "Starting MiroThinker service..."
    nohup python3 -m uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 2 \
        > /var/log/mirothinker.log 2>&1 &

    echo ""
    echo "Waiting for service to start..."
    sleep 3

    # Health check
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        echo "✅ Service is running on port 8000!"
        echo ""
        echo "Access points:"
        echo "  Frontend: http://localhost:8000"
        echo "  API:      http://localhost:8000/api/health"
        echo ""
        echo "Management commands:"
        echo "  View logs:  tail -f /var/log/mirothinker.log"
        echo "  Stop:       pkill -f 'uvicorn main:app'"
    else
        echo "❌ Service failed to start. Check logs:"
        echo "  tail -f /var/log/mirothinker.log"
        exit 1
    fi
fi

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
