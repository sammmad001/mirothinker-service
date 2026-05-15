# MiroThinker 部署规范

## 问题记录

### 2026-05-13 部署路径错误
**问题**：手动使用 `scp` 部署文件到 `/root/mirothinker-service/`，但服务实际运行在 `/opt/mirothinker/`
**影响**：所有修复都没有生效，用户看到的仍是旧版本
**根因**：本地开发目录和服务器运行目录不一致，手动部署时未确认目标路径

## 部署机制

### 1. 唯一正确的部署方式

**永远使用配置化的部署脚本**，禁止手动 scp 单个文件！

```bash
# 正确方式 - 使用部署脚本
cd /Users/sam/Desktop/mirothinker-service
./scripts/deploy.sh production

# 或者使用 Makefile
make deploy
```

### 2. 配置文件位置

`.miro/config.json` 中定义了所有环境的正确路径：

```json
{
  "production": {
    "host": "47.93.253.208",
    "deploy_dir": "/opt/mirothinker",
    "service_name": "mirothinker",
    "health_url": "http://localhost:8001/api/health"
  }
}
```

**任何部署前必须检查此配置文件！**

### 3. 部署前检查清单

- [ ] 确认配置文件中的 `deploy_dir` 路径
- [ ] 确认服务器上的目录存在：`ssh root@47.93.253.208 "ls -la /opt/mirothinker"`
- [ ] 确认服务状态：`ssh root@47.93.253.208 "systemctl status mirothinker"`
- [ ] 确认当前工作目录不是 `/root/mirothinker-service`（这是错误的！）

### 4. 部署后验证

```bash
# 验证静态文件版本
curl -s "http://47.93.253.208/static/js/app.js" | grep "STORAGE_KEY"

# 验证服务响应
curl -s "http://47.93.253.208/" | head -20

# 检查服务日志
ssh root@47.93.253.208 "journalctl -u mirothinker --since '5 minutes ago'"
```

## 目录结构说明

```
本地开发：/Users/sam/Desktop/mirothinker-service/  ← 开发目录
服务器运行：/opt/mirothinker/                     ← 唯一正确的部署目标
错误目录：/root/mirothinker-service/              ← 不要使用！
```

## Makefile 快捷命令

```makefile
# 部署到生产环境
deploy:
	./scripts/deploy.sh production

# 仅部署后端
deploy-backend:
	./scripts/deploy.sh production backend

# 仅部署前端
deploy-frontend:
	./scripts/deploy.sh production frontend

# 验证部署
verify:
	curl -s "http://47.93.253.208/static/js/app.js" | grep "STORAGE_KEY"
	curl -s "http://47.93.253.208/" | head -5

# 重启服务（不部署代码）
restart:
	ssh root@47.93.253.208 "systemctl restart mirothinker"
```

## 紧急修复流程

如果发现问题部署到了错误目录：

1. **立即停止手动 scp**
2. **检查服务实际运行目录**：
   ```bash
   ssh root@47.93.253.208 "ps aux | grep mirothinker | grep -v grep"
   ssh root@47.93.253.208 "ls -la /proc/$(pid)/cwd"
   ```
3. **使用正确的部署脚本**：
   ```bash
   ./scripts/deploy.sh production
   ```
4. **验证部署**：
   ```bash
   curl -s "http://47.93.253.208/static/js/app.js" | head -20
   ```

## 预防措施

1. **在本地 .bashrc 或 .zshrc 中添加别名**：
   ```bash
   alias deploy-miro='cd /Users/sam/Desktop/mirothinker-service && ./scripts/deploy.sh production'
   ```

2. **在 IDE 中添加部署任务配置**（如 VS Code tasks.json）

3. **在 CI/CD 中集成部署脚本**（如果将来使用 GitHub Actions）

4. **定期同步本地和服务器目录结构**：
   ```bash
   # 每月检查一次
   ./scripts/verify-deploy-dir.sh
   ```
