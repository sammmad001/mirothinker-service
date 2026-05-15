#!/usr/bin/env bash
# Deploy pre-check script
# Validates server configuration before deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MiroThinker Deploy Pre-Check${NC}"
echo -e "${BLUE}========================================${NC}"

CONFIG_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.miro/config.json"

# Check config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}✗ Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Config file found: $CONFIG_FILE${NC}"

# Extract server info
PROD_HOST=$(jq -r '.production.host' "$CONFIG_FILE")
PROD_USER=$(jq -r '.production.user' "$CONFIG_FILE")
PROD_DIR=$(jq -r '.production.deploy_dir' "$CONFIG_FILE")

# Validate server address
if [ "$PROD_HOST" = "43.106.52.32" ]; then
    echo -e "${RED}✗ ERROR: Using deprecated server address 43.106.52.32${NC}"
    echo -e "${RED}  Correct address: 47.93.253.208${NC}"
    exit 1
fi

if [ "$PROD_HOST" != "47.93.253.208" ]; then
    echo -e "${YELLOW}⚠ Warning: Server address changed from default${NC}"
    echo -e "${YELLOW}  Current: $PROD_HOST${NC}"
    echo -e "${YELLOW}  Default: 47.93.253.208${NC}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment cancelled${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Server address verified: $PROD_HOST${NC}"

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes "$PROD_USER@$PROD_HOST" "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo -e "${YELLOW}  Please check SSH keys or network connectivity${NC}"
    exit 1
fi

# Show deployment info
echo ""
echo -e "${BLUE}Deployment Summary:${NC}"
echo -e "  Server:  ${GREEN}$PROD_USER@$PROD_HOST${NC}"
echo -e "  Directory: ${GREEN}$PROD_DIR${NC}"
echo -e "  Service: ${GREEN}mirothinker${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All checks passed!${NC}"
echo -e "${GREEN}========================================${NC}"
