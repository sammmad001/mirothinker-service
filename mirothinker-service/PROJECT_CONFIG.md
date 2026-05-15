# MiroThinker 项目配置

## 关键配置信息

### 服务器地址（重要！）
- **正确地址**: `47.93.253.208`
- **错误地址**: `43.106.52.32`（已废弃，网络不可达）
- **权威配置源**: `.miro/config.json`

### 环境配置

| 环境 | 服务器 | 部署目录 | 服务名 | 端口 | 域名 |
|------|--------|----------|--------|------|------|
| 生产 | 47.93.253.208 | /opt/mirothinker | mirothinker | 8001 | mirothinker.sam-ding.com |
| 测试 | 47.93.253.208 | /opt/mirothinker-staging | mirothinker-staging | 8002 | staging.mirothinker.sam-ding.com |

### SSH 连接
- 用户: `root`
- 端口: `22`
- 认证: SSH 密钥（已配置）
- 命令: `ssh -o StrictHostKeyChecking=no root@47.93.253.208`

### 部署命令

#### 快速部署前端
```bash
# 1. 更新版本号（frontend/index.html 中的 v=YYYYMMDDx）
# 2. 部署
scp -o StrictHostKeyChecking=no frontend/js/app.js frontend/index.html root@47.93.253.208:/opt/mirothinker/frontend/
ssh root@47.93.253.208 "systemctl restart nginx"
```

#### 快速部署后端
```bash
scp -o StrictHostKeyChecking=no backend/src/services/agent.py root@47.93.253.208:/opt/mirothinker/backend/src/services/agent.py
ssh root@47.93.253.208 "systemctl restart mirothinker"
```

#### 使用 Makefile（推荐）
```bash
make check-deploy   # 部署前检查
make deploy         # 完整部署
make deploy-backend # 仅后端
make deploy-frontend # 仅前端
make restart        # 重启服务
make check          # 检查状态
```

### 健康检查
```bash
ssh root@47.93.253.208 "curl -s http://localhost:8001/api/health"
```

### 配置文件优先级
1. `.miro/config.json` - **权威配置**（始终优先读取）
2. `Makefile` - 快捷命令
3. `DEPLOY.md` - 详细文档
4. 对话历史/记忆 - 辅助参考

### 注意事项
- 部署前必须运行 `make check-deploy` 验证配置
- 服务器地址变更时，必须同步更新 `.miro/config.json`
- SSH 连接时会显示 post-quantum 警告，可以安全忽略
