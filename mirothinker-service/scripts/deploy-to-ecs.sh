#!/bin/bash
# MiroThinker - Deployment Script for ECS
# Supports deploy, rollback, status, logs, restart, and backup operations
#
# Usage:
#   ./scripts/deploy-to-ecs.sh [command]
#
# Commands:
#   deploy    - Deploy to staging or production
#   rollback  - Rollback to previous version
#   status    - Check service status
#   logs      - View service logs
#   restart   - Restart service
#   backup    - Create manual backup

set -e

# ==========================================
# Configuration
# ==========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/.miro/config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==========================================
# Helper Functions
# ==========================================

print_header() {
    echo -e "\n${BLUE}=========================================${NC}"
    echo -e "${BLUE}  MiroThinker - $1${NC}"
    echo -e "${BLUE}=========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Load configuration from .miro/config.json
load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        print_info "Please create .miro/config.json with server credentials"
        exit 1
    fi

    # Parse JSON config (requires jq)
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed"
        print_info "Install with: brew install jq (macOS) or sudo apt-get install jq (Ubuntu)"
        exit 1
    fi

    ENVIRONMENT="${1:-staging}"

    if [ "$ENVIRONMENT" = "production" ]; then
        SSH_HOST=$(jq -r '.production.host' "$CONFIG_FILE")
        SSH_USER=$(jq -r '.production.user' "$CONFIG_FILE")
        SSH_PASS=$(jq -r '.production.password // empty' "$CONFIG_FILE")
        SSH_KEY=$(jq -r '.production.key // empty' "$CONFIG_FILE")
        DEPLOY_DIR=$(jq -r '.production.deploy_dir' "$CONFIG_FILE")
        SERVICE_NAME=$(jq -r '.production.service_name' "$CONFIG_FILE")
        HEALTH_URL=$(jq -r '.production.health_url' "$CONFIG_FILE")
    else
        SSH_HOST=$(jq -r '.staging.host' "$CONFIG_FILE")
        SSH_USER=$(jq -r '.staging.user' "$CONFIG_FILE")
        SSH_PASS=$(jq -r '.staging.password // empty' "$CONFIG_FILE")
        SSH_KEY=$(jq -r '.staging.key // empty' "$CONFIG_FILE")
        DEPLOY_DIR=$(jq -r '.staging.deploy_dir' "$CONFIG_FILE")
        SERVICE_NAME=$(jq -r '.staging.service_name' "$CONFIG_FILE")
        HEALTH_URL=$(jq -r '.staging.health_url' "$CONFIG_FILE")
    fi

    # Validate required fields
    if [ -z "$SSH_HOST" ] || [ "$SSH_HOST" = "null" ]; then
        print_error "Missing SSH host for $ENVIRONMENT environment"
        exit 1
    fi
}

# Execute command on remote server
ssh_exec() {
    local cmd="$1"

    if [ -n "$SSH_KEY" ] && [ "$SSH_KEY" != "null" ] && [ -f "$SSH_KEY" ]; then
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "$cmd"
    elif [ -n "$SSH_PASS" ] && [ "$SSH_PASS" != "null" ]; then
        # Use sshpass if available
        if command -v sshpass &> /dev/null; then
            sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "$cmd"
        else
            print_error "sshpass is required for password authentication"
            print_info "Install with: brew install hudochenkov/sshpass/sshpass (macOS) or sudo apt-get install sshpass (Ubuntu)"
            exit 1
        fi
    else
        ssh -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "$cmd"
    fi
}

# Copy file to remote server
scp_file() {
    local src="$1"
    local dest="$2"

    if [ -n "$SSH_KEY" ] && [ "$SSH_KEY" != "null" ] && [ -f "$SSH_KEY" ]; then
        scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$src" "$SSH_USER@$SSH_HOST:$dest"
    elif [ -n "$SSH_PASS" ] && [ "$SSH_PASS" != "null" ]; then
        if command -v sshpass &> /dev/null; then
            sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no "$src" "$SSH_USER@$SSH_HOST:$dest"
        else
            print_error "sshpass is required for password authentication"
            exit 1
        fi
    else
        scp -o StrictHostKeyChecking=no "$src" "$SSH_USER@$SSH_HOST:$dest"
    fi
}

# ==========================================
# Commands
# ==========================================

cmd_deploy() {
    local environment="${1:-staging}"
    load_config "$environment"

    print_header "Deploying to $environment"

    # Check if expect is installed (for interactive auth if needed)
    if ! command -v expect &> /dev/null; then
        print_info "expect not found. Password authentication may require sshpass."
    fi

    # Create deployment package
    print_info "Creating deployment package..."
    cd "$PROJECT_DIR"
    TAR_FILE="/tmp/mirothinker-$(date +%Y%m%d%H%M%S).tar.gz"

    tar -czf "$TAR_FILE" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env*' \
        --exclude='data/' \
        --exclude='backups/' \
        --exclude='node_modules/' \
        .

    print_success "Package created: $TAR_FILE"

    # Upload to server
    print_info "Uploading to server..."
    scp_file "$TAR_FILE" "/tmp/mirothinker-latest.tar.gz"
    print_success "Upload complete"

    # Deploy on server
    print_info "Deploying on server..."
    ssh_exec << 'ENDSSH'
set -e

TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR="$DEPLOY_DIR/backups"

# Create directories
mkdir -p $DEPLOY_DIR $BACKUP_DIR

# Backup current version
if [ -d "$DEPLOY_DIR/backend" ]; then
    echo "📦 Creating backup..."
    cp -r $DEPLOY_DIR/backend $BACKUP_DIR/backend.backup.$TIMESTAMP
    # Keep only last 5 backups
    ls -t $BACKUP_DIR/ | tail -n +6 | xargs -r rm -rf
fi

# Extract new version
echo "📥 Extracting new version..."
cd $DEPLOY_DIR
tar -xzf /tmp/mirothinker-latest.tar.gz --strip-components=1

# Apply environment configuration
ENV_FILE="$DEPLOY_DIR/.env"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚙️  Applying production configuration..."
    cp $DEPLOY_DIR/.env.production $ENV_FILE 2>/dev/null || echo "⚠️  .env.production not found"
else
    echo "⚙️  Applying staging configuration..."
    cp $DEPLOY_DIR/.env.staging $ENV_FILE 2>/dev/null || echo "⚠️  .env.staging not found"
fi

# Install dependencies
echo "🔧 Installing dependencies..."
cd $DEPLOY_DIR
pip3 install -r backend/requirements.txt --quiet --upgrade

# Clear Python cache
echo "🧹 Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Restart service
echo "🔄 Restarting service..."
systemctl restart $SERVICE_NAME || true

# Health check
echo "🏥 Running health check..."
sleep 5
if curl -f $HEALTH_URL; then
    echo "✅ Deployment successful!"
else
    echo "❌ Health check failed. Rolling back..."
    rm -rf backend
    cp -r $BACKUP_DIR/backend.backup.$TIMESTAMP backend
    systemctl restart $SERVICE_NAME
    exit 1
fi

# Cleanup
rm -f /tmp/mirothinker-latest.tar.gz
echo "🎉 Deployment complete!"
ENDSSH

    # Cleanup local temp file
    rm -f "$TAR_FILE"
}

cmd_rollback() {
    local environment="${1:-staging}"
    load_config "$environment"

    print_header "Rolling back $environment"

    ssh_exec << 'ENDSSH'
set -e

BACKUP_DIR="$DEPLOY_DIR/backups"

# Find latest backup
LATEST_BACKUP=$(ls -t $BACKUP_DIR/ | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backups found"
    exit 1
fi

echo "📦 Rolling back to: $LATEST_BACKUP"

# Restore backup
rm -rf $DEPLOY_DIR/backend
cp -r $BACKUP_DIR/$LATEST_BACKUP $DEPLOY_DIR/backend

# Restart service
echo "🔄 Restarting service..."
systemctl restart $SERVICE_NAME

# Health check
echo "🏥 Running health check..."
sleep 5
if curl -f $HEALTH_URL; then
    echo "✅ Rollback successful!"
else
    echo "❌ Health check failed after rollback"
    exit 1
fi
ENDSSH
}

cmd_status() {
    local environment="${1:-staging}"
    load_config "$environment"

    print_header "$environment Service Status"

    ssh_exec << 'ENDSSH'
echo "📊 Service Status:"
systemctl status $SERVICE_NAME --no-pager -l || true

echo ""
echo "📦 Disk Usage:"
du -sh $DEPLOY_DIR 2>/dev/null || echo "Deploy dir not found"

echo ""
echo "💾 Backups:"
ls -lh $DEPLOY_DIR/backups/ 2>/dev/null || echo "No backups"
ENDSSH
}

cmd_logs() {
    local environment="${1:-staging}"
    local lines="${2:-100}"
    load_config "$environment"

    print_header "$environment Logs (last $lines lines)"

    ssh_exec "journalctl -u $SERVICE_NAME -n $lines --no-pager"
}

cmd_restart() {
    local environment="${1:-staging}"
    load_config "$environment"

    print_header "Restarting $environment Service"

    ssh_exec << 'ENDSSH'
echo "🔄 Restarting service..."
systemctl restart $SERVICE_NAME

echo "🏥 Running health check..."
sleep 3
if curl -f $HEALTH_URL; then
    echo "✅ Service restarted successfully!"
else
    echo "❌ Health check failed"
    systemctl status $SERVICE_NAME --no-pager -l || true
    exit 1
fi
ENDSSH
}

cmd_backup() {
    local environment="${1:-staging}"
    load_config "$environment"

    print_header "Creating $environment Backup"

    ssh_exec << 'ENDSSH'
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR="$DEPLOY_DIR/backups"

mkdir -p $BACKUP_DIR

echo "📦 Creating backup..."
cp -r $DEPLOY_DIR/backend $BACKUP_DIR/backend.backup.$TIMESTAMP

# Keep only last 5 backups
ls -t $BACKUP_DIR/ | tail -n +6 | xargs -r rm -rf

echo "✅ Backup created: backend.backup.$TIMESTAMP"
echo ""
echo "📦 Current backups:"
ls -lh $BACKUP_DIR/
ENDSSH
}

# ==========================================
# Main
# ==========================================

show_help() {
    echo "MiroThinker Deployment Script"
    echo ""
    echo "Usage:"
    echo "  $0 <command> [environment] [options]"
    echo ""
    echo "Commands:"
    echo "  deploy [staging|production]  - Deploy to environment"
    echo "  rollback [staging|production] - Rollback to previous version"
    echo "  status [staging|production]  - Check service status"
    echo "  logs [staging|production] [N] - View last N lines of logs"
    echo "  restart [staging|production] - Restart service"
    echo "  backup [staging|production]  - Create manual backup"
    echo "  help                         - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 deploy staging"
    echo "  $0 deploy production"
    echo "  $0 rollback production"
    echo "  $0 logs staging 50"
    echo "  $0 status production"
}

COMMAND="${1:-help}"
ENVIRONMENT="${2:-staging}"
shift 2 2>/dev/null || true

case "$COMMAND" in
    deploy)
        cmd_deploy "$ENVIRONMENT" "$@"
        ;;
    rollback)
        cmd_rollback "$ENVIRONMENT" "$@"
        ;;
    status)
        cmd_status "$ENVIRONMENT" "$@"
        ;;
    logs)
        cmd_logs "$ENVIRONMENT" "$@"
        ;;
    restart)
        cmd_restart "$ENVIRONMENT" "$@"
        ;;
    backup)
        cmd_backup "$ENVIRONMENT" "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
