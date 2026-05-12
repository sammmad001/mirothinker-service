#!/usr/bin/env bash
# MiroThinker Service - Backup Script
# Creates backups of data, logs, and configuration

set -e

# Configuration
BACKUP_DIR=${BACKUP_DIR:-./backups}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="mirothinker-backup-${TIMESTAMP}"

echo "========================================"
echo "MiroThinker Service - Backup"
echo "========================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Creating backup: $BACKUP_NAME"

# Backup data directories
echo "Backing up data..."
tar czf "${BACKUP_DIR}/${BACKUP_NAME}-data.tar.gz" \
    data/traces/ \
    data/logs/ \
    data/cache/ \
    2>/dev/null || echo "Warning: Some data directories not found"

# Backup configuration
echo "Backing up configuration..."
tar czf "${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz" \
    .env \
    .env.production \
    docker-compose.yml \
    docker-compose.prod.yml \
    nginx.conf \
    2>/dev/null || echo "Warning: Some config files not found"

# Create backup manifest
cat > "${BACKUP_DIR}/${BACKUP_NAME}-manifest.txt" << EOF
MiroThinker Service Backup
==========================
Date: $(date)
Hostname: $(hostname)
Version: $(grep version pyproject.toml | head -1 | cut -d'"' -f2)

Files:
- ${BACKUP_NAME}-data.tar.gz (traces, logs, cache)
- ${BACKUP_NAME}-config.tar.gz (environment and docker configs)

Notes:
- Keep backups secure (contains API keys)
- Rotate old backups regularly
- Test restore procedure periodically
EOF

echo ""
echo "Backup created in: ${BACKUP_DIR}"
ls -lh "${BACKUP_DIR}/${BACKUP_NAME}"*

# Cleanup old backups (keep last 10)
echo ""
echo "Cleaning up old backups (keeping last 10)..."
cd "$BACKUP_DIR"
ls -t mirothinker-backup-*-data.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
ls -t mirothinker-backup-*-config.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
ls -t mirothinker-backup-*-manifest.txt 2>/dev/null | tail -n +11 | xargs -r rm -f

echo ""
echo "========================================"
echo "Backup Complete!"
echo "========================================"
echo "Backup location: ${BACKUP_DIR}"
echo "Backup name: ${BACKUP_NAME}"
echo ""
