# MiroThinker - Deployment Guide

This guide covers how to deploy and manage MiroThinker in different environments.

## Table of Contents

- [Environments](#environments)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Manual Deployment](#manual-deployment)
- [Rollback](#rollback)
- [Monitoring](#monitoring)
- [Backup & Restore](#backup--restore)

## Environments

| Environment | Purpose | Branch | Domain | Config File |
|------------|---------|--------|--------|-------------|
| Development | Local development | Feature branches | localhost:8000 | `.env.development` |
| Staging | Pre-production testing | `develop` | staging.mirothinker.sam-ding.com | `.env.staging` |
| Production | Live production | `main` + tag | mirothinker.sam-ding.com | `.env.production` |

## Prerequisites

### Local Development

- Python 3.10+
- pip
- Git

### Server Deployment

- Linux server (Ubuntu 20.04+ or CentOS 8+)
- Python 3.11
- pip
- systemd
- Nginx (reverse proxy)
- SSH access

## Local Development

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mirothinker-service
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio pytest-cov  # For testing
```

### 4. Configure Environment

```bash
cp .env.development .env
# Edit .env with your API keys
nano .env
```

### 5. Run Development Server

```bash
cd backend
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

The server will auto-reload on code changes.

### 6. Run Tests

```bash
# Run all tests
pytest backend/tests -v

# Run with coverage
pytest backend/tests --cov=backend/src --cov-report=html

# Run specific test file
pytest backend/tests/test_agent.py -v
```

## Staging Deployment

Staging is automatically deployed when pushing to the `develop` branch.

### Automatic Deployment (CI/CD)

1. Push to develop:
   ```bash
   git push origin develop
   ```

2. GitHub Actions will:
   - Run tests
   - Build artifact
   - Deploy to staging server
   - Run health check

3. Check staging at: `https://staging.mirothinker.sam-ding.com`

### Manual Deployment

```bash
# Deploy to staging
./scripts/deploy-to-ecs.sh deploy staging

# Check status
./scripts/deploy-to-ecs.sh status staging

# View logs
./scripts/deploy-to-ecs.sh logs staging 50
```

## Production Deployment

Production requires a version tag.

### 1. Create Release Branch

```bash
git checkout develop
git checkout -b release/v1.8.0
```

### 2. Update Version and CHANGELOG

Edit `backend/src/core/config.py`:
```python
APP_VERSION: str = "1.8.0"
```

Update `CHANGELOG.md` with all changes.

### 3. Merge to Main and Tag

```bash
git checkout main
git merge --no-ff release/v1.8.0
git tag -a v1.8.0 -m "Release v1.8.0"
git push origin main --tags
```

### 4. Automatic Deployment

GitHub Actions will:
- Run tests
- Build artifact
- Deploy to production server
- Run health check
- Create GitHub Release

### 5. Verify Production

```bash
curl https://mirothinker.sam-ding.com/api/health
```

## Manual Deployment

### Using Deploy Script

```bash
# Deploy to staging
./scripts/deploy-to-ecs.sh deploy staging

# Deploy to production
./scripts/deploy-to-ecs.sh deploy production
```

### Manual Steps

1. SSH to server:
   ```bash
   ssh root@47.108.141.189
   ```

2. Navigate to deploy directory:
   ```bash
   cd /opt/mirothinker
   ```

3. Pull latest code:
   ```bash
   git pull origin main
   ```

4. Apply environment config:
   ```bash
   cp .env.production .env
   ```

5. Install dependencies:
   ```bash
   pip3 install -r backend/requirements.txt --upgrade
   ```

6. Clear Python cache:
   ```bash
   find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
   find . -type f -name "*.pyc" -delete 2>/dev/null || true
   ```

7. Restart service:
   ```bash
   systemctl restart mirothinker
   ```

8. Check status:
   ```bash
   systemctl status mirothinker
   curl http://localhost:8001/api/health
   ```

## Rollback

### Using Deploy Script

```bash
# Rollback staging
./scripts/deploy-to-ecs.sh rollback staging

# Rollback production
./scripts/deploy-to-ecs.sh rollback production
```

### Manual Rollback

1. SSH to server:
   ```bash
   ssh root@47.108.141.189
   ```

2. List backups:
   ```bash
   ls -lh /opt/mirothinker/backups/
   ```

3. Restore latest backup:
   ```bash
   cd /opt/mirothinker
   rm -rf backend
   cp -r backups/backend.backup.YYYYMMDDHHMMSS backend
   ```

4. Restart service:
   ```bash
   systemctl restart mirothinker
   ```

5. Verify:
   ```bash
   curl http://localhost:8001/api/health
   ```

## Monitoring

### Health Check

```bash
curl http://localhost:8001/api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.8.0",
  "dashscope_configured": true,
  "search_available": true,
  "scrape_available": true
}
```

### View Logs

```bash
# Systemd journal
journalctl -u mirothinker -f

# Log file
tail -f /var/log/mirothinker/mirothinker.log

# Last 100 lines
journalctl -u mirothinker -n 100 --no-pager
```

### Service Status

```bash
systemctl status mirothinker
```

### Resource Usage

```bash
# Memory and CPU
top -p $(pgrep -f "uvicorn src.main:app" | tr '\n' ',' | sed 's/,$//')

# Disk usage
du -sh /opt/mirothinker
du -sh /data/mirothinker
```

## Backup & Restore

### Create Backup

```bash
# Using script
./scripts/deploy-to-ecs.sh backup production

# Manual backup
ssh root@47.108.141.189
cd /opt/mirothinker
TIMESTAMP=$(date +%Y%m%d%H%M%S)
cp -r backend backups/backend.backup.$TIMESTAMP
```

### Backup Data Directory

```bash
# Backup database and traces
tar -czf mirothinker-data-$(date +%Y%m%d).tar.gz \
  /data/mirothinker \
  /var/log/mirothinker
```

### Restore Backup

```bash
# Extract backup
cd /opt/mirothinker
tar -xzf mirothinker-data-YYYYMMDD.tar.gz -C /

# Restart service
systemctl restart mirothinker
```

## Configuration Management

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MIRO_ENV` | Environment name | `development`, `staging`, `production` |
| `DASHSCOPE_API_KEY` | Alibaba Bailian API key | `sk-xxx` |
| `DASHSCOPE_BASE_URL` | API base URL | `https://dashscope.aliyuncs.com/...` |
| `PORT` | Server port | `8001` |
| `LOG_LEVEL` | Logging level | `INFO`, `DEBUG` |
| `MAX_CONCURRENT_TASKS` | Max parallel tasks | `2` |

### Server Configuration

Server credentials are stored in `.miro/config.json`:

```json
{
  "production": {
    "host": "47.108.141.189",
    "user": "root",
    "deploy_dir": "/opt/mirothinker",
    "service_name": "mirothinker"
  }
}
```

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   journalctl -u mirothinker -n 50 --no-pager
   ```

2. Verify environment file:
   ```bash
   cat /opt/mirothinker/.env
   ```

3. Check Python dependencies:
   ```bash
   pip3 list | grep -E "fastapi|uvicorn|httpx"
   ```

### Health Check Fails

1. Check if service is running:
   ```bash
   systemctl status mirothinker
   ```

2. Check port binding:
   ```bash
   netstat -tlnp | grep 8001
   ```

3. Check firewall:
   ```bash
   ufw status
   ```

### API Key Issues

1. Verify API key in `.env`:
   ```bash
   echo $DASHSCOPE_API_KEY
   ```

2. Test API key:
   ```bash
   curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
     -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"qwen-flash","messages":[{"role":"user","content":"test"}]}'
   ```

## Quick Reference

```bash
# Deploy
./scripts/deploy-to-ecs.sh deploy [staging|production]

# Rollback
./scripts/deploy-to-ecs.sh rollback [staging|production]

# Status
./scripts/deploy-to-ecs.sh status [staging|production]

# Logs
./scripts/deploy-to-ecs.sh logs [staging|production] [N]

# Restart
./scripts/deploy-to-ecs.sh restart [staging|production]

# Backup
./scripts/deploy-to-ecs.sh backup [staging|production]
```
