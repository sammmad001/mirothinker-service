#!/bin/bash
# MiroThinker 2核2G 优化部署脚本
# 专为低配置服务器设计，限制资源使用

set -e

echo "========================================="
echo "  MiroThinker 2核2G 优化部署"
echo "========================================="
echo ""

# 检查系统资源
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
TOTAL_CPU=$(nproc)

echo "System Resources:"
echo "  CPU Cores: $TOTAL_CPU"
echo "  Total Memory: ${TOTAL_MEM}MB"
echo ""

if [ "$TOTAL_MEM" -lt 1800 ]; then
    echo "⚠️  Warning: Memory is less than 2GB"
    echo "   Using optimized low-memory configuration"
    echo ""
fi

# 选择部署模式
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "Deployment Mode:"
    echo "  1) Docker Compose (Recommended for 2核2G)"
    echo "  2) Direct Python (Lower overhead)"
    echo ""
    read -p "Select mode [1/2]: " mode
else
    echo "Docker not found. Using direct deployment."
    mode="2"
fi

echo ""

if [ "$mode" = "1" ]; then
    # === Docker Compose 部署 ===
    echo "=== Docker Compose Deployment (2核2G Optimized) ==="
    echo ""

    # 检查 .env
    if [ ! -f .env ]; then
        echo "Setting up environment file..."
        cp .env.example .env
        echo ""
        echo "Please edit .env with your API keys:"
        echo "  nano .env"
        echo ""
        read -p "Press Enter after configuring .env..."
    fi

    # 停止旧服务
    echo "Stopping existing service..."
    docker-compose down 2>/dev/null || true

    # 构建并启动
    echo "Building and starting services..."
    docker-compose build --no-cache
    docker-compose up -d

    echo ""
    echo "Waiting for service to start..."
    sleep 8

    # 健康检查
    echo "Running health check..."
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        echo "✅ Service is running!"
        echo ""
        
        # 显示资源限制
        echo "Resource Limits (2核2G Optimized):"
        echo "  CPU: 1.0 core (max)"
        echo "  Memory: 512MB (max)"
        echo "  Workers: 1"
        echo "  Concurrent Tasks: 2 (max)"
        echo ""
        echo "Access points:"
        echo "  Frontend:  http://localhost:8000"
        echo "  API:       http://localhost:8000/api/health"
        echo "  Status:    http://localhost:8000/api/status"
        echo ""
        echo "Management commands:"
        echo "  View logs:     docker-compose logs -f"
        echo "  View stats:    docker stats mirothinker-service"
        echo "  Stop service:  docker-compose down"
        echo "  Restart:       docker-compose restart"
    else
        echo "❌ Service failed to start. Check logs:"
        echo "  docker-compose logs"
        exit 1
    fi

else
    # === 直接部署 ===
    echo "=== Direct Python Deployment (2核2G Optimized) ==="
    echo ""

    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed."
        exit 1
    fi

    echo "Python version: $(python3 --version)"
    echo ""

    # 安装依赖
    echo "Installing dependencies..."
    cd backend
    pip3 install -r requirements.txt --quiet

    # 配置环境
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

    # 加载环境变量
    set -a
    source ../.env
    set +a

    # 停止旧进程
    echo "Stopping existing service (if any)..."
    pkill -f "uvicorn main:app" 2>/dev/null || true
    sleep 2

    # 启动服务 (单 worker，限制并发)
    echo "Starting MiroThinker service (optimized for 2核2G)..."
    nohup python3 -m uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 1 \
        --limit-concurrency 3 \
        --backlog 20 \
        > /var/log/mirothinker.log 2>&1 &

    echo ""
    echo "Waiting for service to start..."
    sleep 3

    # 健康检查
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        echo "✅ Service is running on port 8000!"
        echo ""
        
        # 显示配置
        echo "Configuration (2核2G Optimized):"
        echo "  Workers: 1"
        echo "  Max Concurrency: 3"
        echo "  Max Concurrent Tasks: 2"
        echo ""
        echo "Access points:"
        echo "  Frontend:  http://localhost:8000"
        echo "  API:       http://localhost:8000/api/health"
        echo "  Status:    http://localhost:8000/api/status"
        echo ""
        echo "Management commands:"
        echo "  View logs:   tail -f /var/log/mirothinker.log"
        echo "  View memory: ps aux | grep uvicorn"
        echo "  Stop:        pkill -f 'uvicorn main:app'"
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
echo ""
echo "Next steps:"
echo "  1. Test with a research query"
echo "  2. Monitor resource usage"
echo "  3. Configure Nginx (optional)"
echo ""
