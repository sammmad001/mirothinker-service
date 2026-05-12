#!/usr/bin/env bash
# MiroThinker Service - Deploy Script
# Deploys the application to a server via SSH (password or key auth)
# Usage: ./scripts/deploy.sh [staging|production]

set -e

ENVIRONMENT="${1:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/.miro/config.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MiroThinker - ${ENVIRONMENT} Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo -e "${RED}jq required: brew install jq${NC}"
    exit 1
fi

# Load config
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Config not found: $CONFIG_FILE${NC}"
    exit 1
fi

if [ "$ENVIRONMENT" = "production" ]; then
    SSH_HOST=$(jq -r '.production.host' "$CONFIG_FILE")
    SSH_USER=$(jq -r '.production.user' "$CONFIG_FILE")
    SSH_PASS=$(jq -r '.production.password' "$CONFIG_FILE")
    SSH_KEY=$(jq -r '.production.key' "$CONFIG_FILE")
    DEPLOY_DIR=$(jq -r '.production.deploy_dir' "$CONFIG_FILE")
    SERVICE_NAME=$(jq -r '.production.service_name' "$CONFIG_FILE")
    HEALTH_URL=$(jq -r '.production.health_url' "$CONFIG_FILE")
else
    SSH_HOST=$(jq -r '.staging.host' "$CONFIG_FILE")
    SSH_USER=$(jq -r '.staging.user' "$CONFIG_FILE")
    SSH_PASS=$(jq -r '.staging.password' "$CONFIG_FILE")
    SSH_KEY=$(jq -r '.staging.key' "$CONFIG_FILE")
    DEPLOY_DIR=$(jq -r '.staging.deploy_dir' "$CONFIG_FILE")
    SERVICE_NAME=$(jq -r '.staging.service_name' "$CONFIG_FILE")
    HEALTH_URL=$(jq -r '.staging.health_url' "$CONFIG_FILE")
fi

echo -e "${YELLOW}Target: ${SSH_USER}@${SSH_HOST}:${DEPLOY_DIR}${NC}"

# Build SSH options
SSH_OPTS="-o StrictHostKeyChecking=no"
if [ -n "$SSH_KEY" ] && [ "$SSH_KEY" != "null" ] && [ -f "$SSH_KEY" ]; then
    SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
elif command -v sshpass &> /dev/null && [ -n "$SSH_PASS" ] && [ "$SSH_PASS" != "null" ]; then
    SSH_CMD_PREFIX="sshpass -p '$SSH_PASS'"
else
    echo -e "${YELLOW}No SSH key or sshpass. Will prompt for password.${NC}"
    SSH_CMD_PREFIX=""
fi

SSH_EXEC="${SSH_CMD_PREFIX:-} ssh $SSH_OPTS ${SSH_USER}@${SSH_HOST}"

# Create tarball
TIMESTAMP=$(date +%Y%m%d%H%M%S)
ARCHIVE="mirothinker-${TIMESTAMP}.tar.gz"

echo -e "${YELLOW}Creating deployment package...${NC}"
cd "$PROJECT_DIR"
tar czf "/tmp/$ARCHIVE" \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.ruff_cache' \
    --exclude='data/' \
    --exclude='backups/' \
    --exclude='.DS_Store' \
    --exclude='.miro/config.json' \
    backend/ frontend/ scripts/ docs/ \
    Dockerfile docker-compose.yml \
    nginx.conf pyproject.toml Makefile .dockerignore \
    .env.example .env.staging .env.production

echo -e "${GREEN}Package: $ARCHIVE ($(du -h "/tmp/$ARCHIVE" | cut -f1))${NC}"

# Upload
echo -e "${YELLOW}Uploading to server...${NC}"
SCP_CMD="${SSH_CMD_PREFIX:-} scp $SSH_OPTS /tmp/$ARCHIVE ${SSH_USER}@${SSH_HOST}:/tmp/"
eval "$SCP_CMD"

# Deploy
echo -e "${YELLOW}Deploying on remote server...${NC}"
eval "$SSH_EXEC" << EOF
set -e

echo "Extracting package..."
mkdir -p $DEPLOY_DIR
tar xzf /tmp/$ARCHIVE -C $DEPLOY_DIR --strip-components=0

echo "Setting up environment..."
cd $DEPLOY_DIR
cp .env.$ENVIRONMENT .env 2>/dev/null || echo "Using existing .env"

echo "Installing dependencies..."
pip3 install -r backend/requirements.txt --upgrade --quiet 2>/dev/null || true

echo "Clearing cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "Restarting service..."
systemctl restart $SERVICE_NAME 2>/dev/null || echo "Service not managed by systemd"

sleep 3

echo "Health check..."
if curl -f -s $HEALTH_URL > /dev/null 2>&1; then
    echo "SUCCESS"
    curl -s $HEALTH_URL
else
    echo "WARNING: Health check failed"
fi

rm -f /tmp/$ARCHIVE
echo "Done!"
EOF

rm -f "/tmp/$ARCHIVE"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Health: $HEALTH_URL"
