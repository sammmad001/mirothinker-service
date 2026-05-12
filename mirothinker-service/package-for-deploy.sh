#!/bin/bash
# =============================================================================
# MiroThinker 项目打包脚本
# 用途：打包项目以便上传到云服务器
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_DIR="/Users/sam/Desktop/mirothinker-service"
OUTPUT_DIR="/Users/sam/Desktop"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="mirothinker-service-${TIMESTAMP}.tar.gz"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

main() {
    echo ""
    log_info "=========================================="
    log_info "MiroThinker 项目打包脚本"
    log_info "=========================================="
    echo ""

    cd "$PROJECT_DIR"

    # 检查必要文件
    log_info "检查必要文件..."
    local required_files=("Dockerfile" "docker-compose.yml" "nginx.conf" ".env.example" "backend/main.py" "frontend/index.html")

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "缺少必要文件: $file"
            exit 1
        fi
    done
    log_success "所有必要文件已就绪"

    # 创建 .dockerignore (如果不存在)
    if [ ! -f ".dockerignore" ]; then
        log_info "创建 .dockerignore..."
        cat > .dockerignore << 'EOF'
.git
.gitignore
.env
*.md
!README.md
.DS_Store
node_modules
__pycache__
*.pyc
traces
logs
cache
benchmarks
certs
backups
*.tar.gz
EOF
        log_success ".dockerignore 创建完成"
    fi

    # 清理不必要的文件
    log_info "清理临时文件..."
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name ".DS_Store" -delete 2>/dev/null || true

    # 打包项目 (排除不必要的文件)
    log_info "打包项目..."
    cd /Users/sam/Desktop

    tar czf "$OUTPUT_DIR/$ARCHIVE_NAME" \
        --exclude='mirothinker-service/.git' \
        --exclude='mirothinker-service/.env' \
        --exclude='mirothinker-service/production.env' \
        --exclude='mirothinker-service/traces' \
        --exclude='mirothinker-service/logs' \
        --exclude='mirothinker-service/cache' \
        --exclude='mirothinker-service/benchmarks' \
        --exclude='mirothinker-service/certs' \
        --exclude='mirothinker-service/__pycache__' \
        --exclude='mirothinker-service/*.pyc' \
        --exclude='mirothinker-service/.DS_Store' \
        mirothinker-service

    log_success "打包完成: $OUTPUT_DIR/$ARCHIVE_NAME"
    log_info "文件大小: $(du -sh "$OUTPUT_DIR/$ARCHIVE_NAME" | cut -f1)"

    # 显示上传说明
    echo ""
    log_info "=========================================="
    log_info "上传到云端服务器"
    log_info "=========================================="
    echo ""
    log_info "方法 1: SCP 上传"
    log_info "  scp $OUTPUT_DIR/$ARCHIVE_NAME user@server-ip:~/"
    log_info "  ssh user@server-ip 'tar xzf $ARCHIVE_NAME && rm $ARCHIVE_NAME'"
    echo ""
    log_info "方法 2: Rsync 上传"
    log_info "  rsync -avz --progress $PROJECT_DIR/ user@server-ip:~/mirothinker-service/"
    echo ""
    log_info "方法 3: Git 推送"
    log_info "  cd $PROJECT_DIR"
    log_info "  git add ."
    log_info "  git commit -m 'Ready for deployment'"
    log_info "  git push"
    echo ""
    log_info "云端服务器执行:"
    log_info "  cd ~/mirothinker-service"
    log_info "  cp .env.example .env"
    log_info "  nano .env  # 配置 API Key"
    log_info "  chmod +x cloud-deploy.sh"
    log_info "  ./cloud-deploy.sh"
    echo ""
}

main "$@"
