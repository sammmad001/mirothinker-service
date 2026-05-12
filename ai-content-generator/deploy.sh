#!/bin/bash

# ContentAI 部署脚本
# 部署到 Netlify

echo "🚀 开始部署 ContentAI..."

# 检查netlify CLI
if ! command -v netlify &> /dev/null; then
    echo "📦 安装 Netlify CLI..."
    npm install -g netlify-cli
fi

# 登录Netlify（需要API Token）
echo "⚠️  如果未登录，请设置 NETLIFY_AUTH_TOKEN 环境变量"

# 部署
echo "📤 部署到 Netlify..."
cd /Users/sam/Desktop/ai-content-generator

netlify deploy --prod --dir=dist

echo "✅ 部署完成！"
echo ""
echo "📝 下一步："
echo "1. 访问 Netlify Dashboard 创建 Stripe/Paddle 集成"
echo "2. 添加自定义域名"
echo "3. 配置 Google Analytics"
echo "4. 发布到 Product Hunt"
