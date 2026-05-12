#!/usr/bin/env bash
# MiroThinker Service - Deploy Script
# Deploys the application to a remote server via SSH

set -e

# Configuration
REMOTE_USER=${REMOTE_USER:-root}
REMOTE_HOST=${REMOTE_HOST:?Error: REMOTE_HOST is required}
REMOTE_PORT=${REMOTE_PORT:-22}
REMOTE_DIR=${REMOTE_DIR:-/root/mirothinker-service}
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

echo "========================================"
echo "MiroThinker Service - Deployment"
echo "========================================"
echo "Target: $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"
echo ""

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "Error: .env.production not found"
    echo "Please create .env.production with production environment variables"
    exit 1
fi

# Create tarball
echo "Creating deployment package..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE="mirothinker-${TIMESTAMP}.tar.gz"

tar czf "$ARCHIVE" \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.ruff_cache' \
    --exclude='data/traces' \
    --exclude='data/logs' \
    --exclude='data/cache' \
    --exclude='.DS_Store' \
    backend/ frontend/ scripts/ docs/ \
    Dockerfile docker-compose.yml docker-compose.prod.yml \
    nginx.conf pyproject.toml Makefile .dockerignore \
    .env.production

echo "Package created: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

# Upload to server
echo "Uploading to server..."
scp -P "$REMOTE_PORT" -i "$SSH_KEY" "$ARCHIVE" "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Deploy on server
echo "Deploying on remote server..."
ssh -P "$REMOTE_PORT" -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" << EOF
set -e

echo "Extracting package..."
mkdir -p $REMOTE_DIR
tar xzf /tmp/$ARCHIVE -C $REMOTE_DIR --strip-components=0

echo "Setting up environment..."
cd $REMOTE_DIR
cp .env.production .env

echo "Building and starting services..."
docker compose -f docker-compose.prod.yml down || true
docker compose -f docker-compose.prod.yml up -d --build

echo "Waiting for services to start..."
sleep 10

echo "Checking health..."
curl -f http://localhost:8000/api/health || echo "Warning: Health check failed"

echo "Cleaning up..."
rm -f /tmp/$ARCHIVE

echo "Deployment complete!"
EOF

# Cleanup
rm -f "$ARCHIVE"

echo ""
echo "========================================"
echo "Deployment Successful!"
echo "========================================"
echo "Service: http://$REMOTE_HOST"
echo "Health:  http://$REMOTE_HOST/api/health"
echo ""
