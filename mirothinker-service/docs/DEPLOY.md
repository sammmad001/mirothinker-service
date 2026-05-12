# Deployment Guide

Complete guide for deploying MiroThinker Online Service to production.

## Prerequisites

- Docker 20.10+
- Docker Compose v2.0+
- Server with minimum 2GB RAM (2 CPU cores recommended)
- Alibaba Bailian API key

## Local Development

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd mirothinker-service

# Run setup script
./scripts/setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev,monitoring]"
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit and add your API key
nano .env
```

Required variables:
```env
DASHSCOPE_API_KEY=sk-sp-djI.40I_n****2_mku5GC5ROILIY
```

### 3. Start Development Server

```bash
# Using Makefile
make run

# Or using script
./scripts/start.sh dev

# Or directly
cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000

## Docker Deployment

### 1. Build and Start

```bash
# Build and start all services
make docker-up
# Or: docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f app
docker compose logs -f nginx
```

### 2. Verify Deployment

```bash
# Health check
curl http://localhost/api/health

# System status
curl http://localhost/api/status

# Test research
curl -X POST http://localhost/api/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}'
```

### 3. Stop Services

```bash
make docker-down
# Or: docker compose down
```

## Production Deployment

### Option 1: Automated Deploy Script

```bash
# Set environment variables
export REMOTE_HOST=47.93.253.208
export REMOTE_USER=root

# Run deployment
./scripts/deploy.sh
```

### Option 2: Manual Deployment

#### 1. Server Preparation

```bash
# SSH to server
ssh root@47.93.253.208

# Install Docker (if not installed)
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt-get install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

#### 2. Upload Files

```bash
# From local machine
scp -r mirothinker-service/ root@47.93.253.208:/root/

# Or create tarball
tar czf mirothinker.tar.gz mirothinker-service/
scp mirothinker.tar.gz root@47.93.253.208:/root/

# On server
cd /root
tar xzf mirothinker.tar.gz
cd mirothinker-service
```

#### 3. Configure Environment

```bash
# On server
cd /root/mirothinker-service

# Create production environment
cp .env.example .env
nano .env
```

Production `.env`:
```env
DASHSCOPE_API_KEY=your_production_api_key
DEBUG=false
WORKERS=1
MAX_CONCURRENT_TASKS=2
```

#### 4. Start Services

```bash
# Using production compose file
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to start
sleep 15

# Check health
curl http://localhost/api/health
```

#### 5. Setup SSL (Optional but Recommended)

```bash
# Install Certbot
apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot certonly --standalone -d your-domain.com

# Configure Nginx with SSL
# Edit nginx.conf to include SSL settings

# Restart Nginx
docker compose -f docker-compose.prod.yml restart nginx
```

## Monitoring

### Check Service Status

```bash
# Container status
docker compose ps

# Resource usage
docker stats

# Application logs
docker compose logs -f --tail=100 app
```

### Health Monitoring

```bash
# Continuous health check
while true; do
  curl -s http://localhost/api/health | jq .
  sleep 30
done
```

### Log Management

Logs are stored in:
- Container logs: `docker compose logs`
- Application logs: `data/logs/mirothinker.log`
- Nginx logs: Docker json-file driver

### Backup

```bash
# Run backup script
./scripts/backup.sh

# Backup location: ./backups/
# Contains: data, configuration, manifest
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs app

# Common issues:
# 1. API key not configured
# 2. Port already in use
# 3. Insufficient memory
```

### High Memory Usage

```bash
# Check memory
docker stats

# Optimize: Reduce WORKERS to 1 in .env
# Optimize: Reduce MAX_CONCURRENT_TASKS to 1
```

### API Returns 502

```bash
# Check if app container is running
docker compose ps

# Restart app
docker compose restart app

# Check app logs
docker compose logs --tail=50 app
```

## Rollback

```bash
# Stop current deployment
docker compose -f docker-compose.prod.yml down

# Restore from backup
tar xzf backups/mirothinker-backup-YYYYMMDD-config.tar.gz

# Restart
docker compose -f docker-compose.prod.yml up -d
```

## Performance Tuning

### For 2GB Server

```env
# .env
WORKERS=1
MAX_CONCURRENT_TASKS=2
```

### For 4GB Server

```env
# .env
WORKERS=2
MAX_CONCURRENT_TASKS=4
```

### For 8GB+ Server

```env
# .env
WORKERS=4
MAX_CONCURRENT_TASKS=8
```

## Security Checklist

- [ ] API keys configured and not committed to Git
- [ ] SSL/TLS enabled for production
- [ ] Firewall rules configured (only 80/443 open)
- [ ] Docker container running as non-root user
- [ ] Regular backups scheduled
- [ ] Logs monitored for suspicious activity
- [ ] Dependencies updated regularly
