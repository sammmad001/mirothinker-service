#!/bin/bash
# =============================================================================
# MiroThinker 云端一键部署脚本
# 用途：在云服务器上自动部署 MiroThinker 服务
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_DIR="${HOME}/mirothinker-service"
BACKUP_DIR="${HOME}/backups/mirothinker"
DOMAIN="${MIRO_DOMAIN:-}"
EMAIL="${LETSENCRYPT_EMAIL:-}"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查函数
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_error "请不要使用 root 用户运行此脚本"
        exit 1
    fi
}

check_dependencies() {
    log_info "检查系统依赖..."

    local deps=("docker" "docker-compose" "git" "curl")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_warning "缺少以下依赖: ${missing[*]}"
        log_info "正在安装缺失依赖..."
        install_dependencies
    else
        log_success "所有依赖已就绪"
    fi
}

install_dependencies() {
    local OS=$(cat /etc/os-release 2>/dev/null | grep "^ID=" | cut -d'=' -f2 | tr -d '"')

    case "$OS" in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y docker.io docker-compose git curl
            ;;
        centos|rhel|fedora)
            sudo yum install -y docker docker-compose git curl
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac

    # 启动 Docker 服务
    sudo systemctl start docker
    sudo systemctl enable docker

    # 添加当前用户到 docker 组
    sudo usermod -aG docker $USER

    log_success "依赖安装完成，请重新登录以生效 docker 组权限"
    exit 0
}

# 备份函数
backup_existing() {
    if [ -d "$PROJECT_DIR" ]; then
        log_info "备份现有部署..."
        mkdir -p "$BACKUP_DIR"
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_path="${BACKUP_DIR}/backup_${timestamp}"

        cp -r "$PROJECT_DIR" "$backup_path"
        log_success "备份完成: $backup_path"

        # 保留最近 5 个备份
        cd "$BACKUP_DIR"
        ls -dt backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
        cd - > /dev/null
    fi
}

# 部署函数
deploy_service() {
    log_info "部署 MiroThinker 服务..."

    # 创建必要目录
    mkdir -p "$PROJECT_DIR"/{traces,logs,cache,benchmarks,certs}

    # 进入项目目录
    cd "$PROJECT_DIR"

    # 停止现有服务
    docker-compose down || true

    # 拉取最新代码 (如果使用 Git)
    if [ -d ".git" ]; then
        log_info "拉取最新代码..."
        git pull || log_warning "Git pull 失败，跳过"
    fi

    # 检查 .env 文件
    if [ ! -f ".env" ]; then
        log_error "未找到 .env 文件！"
        log_info "请先创建 .env 文件并配置环境变量"
        log_info "参考模板: .env.example"
        exit 1
    fi

    # 构建并启动服务
    log_info "构建 Docker 镜像..."
    docker-compose build

    log_info "启动服务..."
    docker-compose up -d

    # 等待服务就绪
    log_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "服务启动成功！"
    else
        log_error "服务启动失败，请查看日志"
        docker-compose logs
        exit 1
    fi
}

# SSL 证书配置
setup_ssl() {
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        log_warning "未配置域名或邮箱，跳过 SSL 配置"
        log_info "如需配置 SSL，请设置环境变量:"
        log_info "  export MIRO_DOMAIN=your-domain.com"
        log_info "  export LETSENCRYPT_EMAIL=your@email.com"
        return 0
    fi

    log_info "配置 Let's Encrypt SSL 证书..."

    # 安装 certbot
    if ! command -v certbot &> /dev/null; then
        sudo apt-get install -y certbot python3-certbot-nginx 2>/dev/null || \
        sudo yum install -y certbot python3-certbot-nginx 2>/dev/null || \
        log_warning "certbot 安装失败，请手动安装"
    fi

    # 申请证书
    sudo certbot certonly --standalone \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive \
        --keep-until-expiring || log_warning "证书申请失败"

    # 复制证书到项目目录
    if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        mkdir -p "$PROJECT_DIR/certs"
        sudo cp /etc/letsencrypt/live/"$DOMAIN"/* "$PROJECT_DIR/certs/"
        sudo chown $USER:$USER "$PROJECT_DIR/certs/"*
        log_success "SSL 证书配置完成"
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    local max_retries=30
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if curl -sf http://localhost:80/api/health > /dev/null 2>&1; then
            log_success "健康检查通过！"
            return 0
        fi

        retry_count=$((retry_count + 1))
        sleep 2
    done

    log_error "健康检查失败，服务可能未完全启动"
    return 1
}

# 显示部署信息
show_info() {
    echo ""
    log_success "=========================================="
    log_success "MiroThinker 部署完成！"
    log_success "=========================================="
    echo ""
    log_info "访问地址: http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'localhost')"
    log_info "API 地址: http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'localhost')/api/health"
    echo ""
    log_info "管理命令:"
    log_info "  查看日志: cd $PROJECT_DIR && docker-compose logs -f"
    log_info "  停止服务: cd $PROJECT_DIR && docker-compose down"
    log_info "  重启服务: cd $PROJECT_DIR && docker-compose restart"
    log_info "  更新服务: cd $PROJECT_DIR && ./deploy.sh"
    echo ""
    log_info "备份命令:"
    log_info "  执行备份: cd $PROJECT_DIR && ./backup.sh"
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "=========================================="
    log_info "MiroThinker 云端部署脚本"
    log_info "=========================================="
    echo ""

    check_root
    check_dependencies
    backup_existing
    deploy_service
    setup_ssl
    health_check
    show_info
}

# 执行主函数
main "$@"
