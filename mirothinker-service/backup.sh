#!/bin/bash
# =============================================================================
# MiroThinker 数据备份脚本
# 用途：备份研究数据、日志、配置等关键文件
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
BACKUP_BASE_DIR="${HOME}/backups/mirothinker"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE_DIR}/backup_${TIMESTAMP}"

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

# 创建备份目录结构
setup_backup_dir() {
    mkdir -p "$BACKUP_DIR"/{traces,logs,cache,config,certs}
    log_success "备份目录创建完成: $BACKUP_DIR"
}

# 备份数据文件
backup_data() {
    log_info "开始备份数据..."

    # 备份 traces (研究追踪数据)
    if [ -d "$PROJECT_DIR/traces" ] && [ "$(ls -A $PROJECT_DIR/traces 2>/dev/null)" ]; then
        log_info "备份 traces..."
        cp -r "$PROJECT_DIR/traces/"* "$BACKUP_DIR/traces/"
        log_success "traces 备份完成"
    else
        log_warning "traces 目录为空，跳过"
    fi

    # 备份 logs (日志文件)
    if [ -d "$PROJECT_DIR/logs" ] && [ "$(ls -A $PROJECT_DIR/logs 2>/dev/null)" ]; then
        log_info "备份 logs..."
        cp -r "$PROJECT_DIR/logs/"* "$BACKUP_DIR/logs/"
        log_success "logs 备份完成"
    else
        log_warning "logs 目录为空，跳过"
    fi

    # 备份 cache (缓存数据)
    if [ -d "$PROJECT_DIR/cache" ] && [ "$(ls -A $PROJECT_DIR/cache 2>/dev/null)" ]; then
        log_info "备份 cache..."
        cp -r "$PROJECT_DIR/cache/"* "$BACKUP_DIR/cache/"
        log_success "cache 备份完成"
    else
        log_warning "cache 目录为空，跳过"
    fi

    # 备份 benchmarks (基准测试数据)
    if [ -d "$PROJECT_DIR/benchmarks" ] && [ "$(ls -A $PROJECT_DIR/benchmarks 2>/dev/null)" ]; then
        log_info "备份 benchmarks..."
        cp -r "$PROJECT_DIR/benchmarks/"* "$BACKUP_DIR/benchmarks/"
        log_success "benchmarks 备份完成"
    else
        log_warning "benchmarks 目录为空，跳过"
    fi
}

# 备份配置文件
backup_config() {
    log_info "备份配置文件..."

    # 备份 .env (环境变量，排除敏感信息)
    if [ -f "$PROJECT_DIR/.env" ]; then
        log_info "备份 .env (已脱敏)..."
        grep -v "API_KEY\|SECRET\|PASSWORD" "$PROJECT_DIR/.env" > "$BACKUP_DIR/config/.env.template" || \
        cp "$PROJECT_DIR/.env" "$BACKUP_DIR/config/.env.backup"
        log_success ".env 备份完成"
    fi

    # 备份 docker-compose.yml
    if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
        cp "$PROJECT_DIR/docker-compose.yml" "$BACKUP_DIR/config/"
        log_success "docker-compose.yml 备份完成"
    fi

    # 备份 nginx.conf
    if [ -f "$PROJECT_DIR/nginx.conf" ]; then
        cp "$PROJECT_DIR/nginx.conf" "$BACKUP_DIR/config/"
        log_success "nginx.conf 备份完成"
    fi

    # 备份 Dockerfile
    if [ -f "$PROJECT_DIR/Dockerfile" ]; then
        cp "$PROJECT_DIR/Dockerfile" "$BACKUP_DIR/config/"
        log_success "Dockerfile 备份完成"
    fi
}

# 备份 SSL 证书
backup_certs() {
    if [ -d "$PROJECT_DIR/certs" ] && [ "$(ls -A $PROJECT_DIR/certs 2>/dev/null)" ]; then
        log_info "备份 SSL 证书..."
        cp -r "$PROJECT_DIR/certs/"* "$BACKUP_DIR/certs/"
        chmod 600 "$BACKUP_DIR/certs/"* 2>/dev/null || true
        log_success "SSL 证书备份完成"
    else
        log_warning "SSL 证书目录为空，跳过"
    fi
}

# 备份 Docker 数据库卷 (如果有)
backup_volumes() {
    log_info "检查 Docker volumes..."

    # 列出相关 volumes
    local volumes=$(docker volume ls --format "{{.Name}}" | grep -i mirothinker 2>/dev/null || true)

    if [ -n "$volumes" ]; then
        log_info "备份 Docker volumes..."
        for volume in $volumes; do
            log_info "备份 volume: $volume"
            docker run --rm \
                -v "$volume":/source:ro \
                -v "$BACKUP_DIR:/backup" \
                alpine tar czf "/backup/${volume}.tar.gz" -C /source .
            log_success "volume $volume 备份完成"
        done
    else
        log_info "未找到相关 Docker volumes，跳过"
    fi
}

# 创建备份摘要
create_summary() {
    log_info "生成备份摘要..."

    cat > "$BACKUP_DIR/BACKUP_INFO.txt" << EOF
MiroThinker Backup Summary
==========================

Backup Time: $(date '+%Y-%m-%d %H:%M:%S')
Backup Directory: $BACKUP_DIR
Project Directory: $PROJECT_DIR

Backup Contents:
$(du -sh "$BACKUP_DIR"/* 2>/dev/null || echo "No data")

Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)

Docker Service Status:
$(docker-compose -f "$PROJECT_DIR/docker-compose.yml" ps 2>/dev/null || echo "Service not running")

Docker Images:
$(docker images | grep mirothinker 2>/dev/null || echo "No mirothinker images")

EOF

    log_success "备份摘要生成完成"
}

# 压缩备份
compress_backup() {
    log_info "压缩备份文件..."

    local archive="${BACKUP_BASE_DIR}/mirothinker_backup_${TIMESTAMP}.tar.gz"

    cd "$BACKUP_BASE_DIR"
    tar czf "$archive" "backup_${TIMESTAMP}"

    log_success "压缩完成: $archive"
    log_info "压缩后大小: $(du -sh "$archive" | cut -f1)"

    # 清理未压缩目录
    rm -rf "$BACKUP_DIR"
    log_info "临时目录已清理"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份 (保留最近 10 个)..."

    cd "$BACKUP_BASE_DIR"
    local count=$(ls -1 mirothinker_backup_*.tar.gz 2>/dev/null | wc -l)

    if [ "$count" -gt 10 ]; then
        ls -1t mirothinker_backup_*.tar.gz | tail -n +11 | xargs rm -f
        log_info "已清理 $((count - 10)) 个旧备份"
    else
        log_info "当前备份数量: $count，无需清理"
    fi
}

# 显示备份信息
show_backup_info() {
    echo ""
    log_success "=========================================="
    log_success "备份完成！"
    log_success "=========================================="
    echo ""
    log_info "备份文件: ${BACKUP_BASE_DIR}/mirothinker_backup_${TIMESTAMP}.tar.gz"
    log_info "备份大小: $(du -sh "${BACKUP_BASE_DIR}/mirothinker_backup_${TIMESTAMP}.tar.gz" | cut -f1)"
    echo ""
    log_info "恢复命令:"
    log_info "  cd ${BACKUP_BASE_DIR}"
    log_info "  tar xzf mirothinker_backup_${TIMESTAMP}.tar.gz -C /tmp/"
    log_info "  cp -r /tmp/backup_${TIMESTAMP}/* ${PROJECT_DIR}/"
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "=========================================="
    log_info "MiroThinker 数据备份脚本"
    log_info "=========================================="
    echo ""

    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi

    # 创建备份基础目录
    mkdir -p "$BACKUP_BASE_DIR"

    setup_backup_dir
    backup_data
    backup_config
    backup_certs
    backup_volumes
    create_summary
    compress_backup
    cleanup_old_backups
    show_backup_info
}

# 执行主函数
main "$@"
