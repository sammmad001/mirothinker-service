#!/bin/bash
# 验证部署目录一致性
# 检查本地配置和服务器实际运行目录是否匹配

set -e

CONFIG_FILE="/Users/sam/Desktop/mirothinker-service/.miro/config.json"
SERVER="root@47.93.253.208"

echo "=========================================="
echo "  MiroThinker 部署目录验证"
echo "=========================================="
echo ""

# 检查配置文件
echo "1. 检查配置文件..."
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 提取配置中的部署目录
DEPLOY_DIR=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['production']['deploy_dir'])" 2>/dev/null || \
             jq -r '.production.deploy_dir' "$CONFIG_FILE" 2>/dev/null)

if [ -z "$DEPLOY_DIR" ] || [ "$DEPLOY_DIR" = "null" ]; then
    echo "❌ 配置文件中未找到 production.deploy_dir"
    exit 1
fi

echo "   配置中的部署目录: $DEPLOY_DIR"
echo ""

# 检查服务器连接
echo "2. 检查服务器连接..."
if ! ssh -o ConnectTimeout=5 "$SERVER" "echo OK" > /dev/null 2>&1; then
    echo "❌ 无法连接到服务器 $SERVER"
    exit 1
fi
echo "   ✓ 服务器连接正常"
echo ""

# 检查服务器上的部署目录
echo "3. 检查服务器部署目录..."
if ! ssh "$SERVER" "test -d $DEPLOY_DIR && echo EXISTS"; then
    echo "❌ 部署目录不存在: $DEPLOY_DIR"
    exit 1
fi
echo "   ✓ 部署目录存在: $DEPLOY_DIR"
echo ""

# 检查服务运行目录
echo "4. 检查服务实际运行目录..."
PID=$(ssh "$SERVER" "pgrep -f 'uvicorn.*mirothinker' | head -1")
if [ -z "$PID" ]; then
    echo "   ⚠ 未找到运行中的服务进程"
else
    CWD=$(ssh "$SERVER" "readlink /proc/$PID/cwd 2>/dev/null || pwdx $PID 2>/dev/null | awk '{print \$2}'")
    echo "   服务进程 PID: $PID"
    echo "   服务运行目录: $CWD"
    
    if [ "$CWD" != "$DEPLOY_DIR" ] && [ -n "$CWD" ]; then
        echo "   ❌ 警告：服务运行目录与配置不一致！"
        echo "      配置: $DEPLOY_DIR"
        echo "      实际: $CWD"
        exit 1
    fi
    echo "   ✓ 运行目录与配置一致"
fi
echo ""

# 检查前端目录
echo "5. 检查前端文件..."
FRONTEND_DIR="$DEPLOY_DIR/frontend"
if ssh "$SERVER" "test -d $FRONTEND_DIR && test -f $FRONTEND_DIR/index.html"; then
    echo "   ✓ 前端文件存在"
    
    # 检查版本号
    VERSION=$(ssh "$SERVER" "grep -o 'v=[0-9]*' $FRONTEND_DIR/index.html | head -1")
    echo "   当前版本: $VERSION"
else
    echo "   ❌ 前端文件缺失"
    exit 1
fi
echo ""

# 检查后端文件
echo "6. 检查后端文件..."
BACKEND_DIR="$DEPLOY_DIR/backend"
if ssh "$SERVER" "test -d $BACKEND_DIR && test -f $BACKEND_DIR/main.py"; then
    echo "   ✓ 后端文件存在"
else
    echo "   ❌ 后端文件缺失"
    exit 1
fi
echo ""

echo "=========================================="
echo "  ✓ 所有检查通过！"
echo "=========================================="
echo ""
echo "部署目录验证完成，可以安全使用 ./scripts/deploy.sh 进行部署"
