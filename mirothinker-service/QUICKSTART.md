# MiroThinker - 开发流程快速参考

## 环境隔离架构

```
┌─────────────────────────────────────────────────────────────┐
│                    开发环境 (Development)                     │
│  分支: feature/*                                           │
│  配置: .env.development                                     │
│  运行: localhost:8000                                       │
│  测试: pytest backend/tests                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓ PR
┌─────────────────────────────────────────────────────────────┐
│                    预发布环境 (Staging)                       │
│  分支: develop                                              │
│  配置: .env.staging                                         │
│  部署: 自动 (push to develop)                               │
│  域名: staging.mirothinker.sam-ding.com                     │
└─────────────────────────────────────────────────────────────┘
                          ↓ Release
┌─────────────────────────────────────────────────────────────┐
│                    生产环境 (Production)                      │
│  分支: main + tag (v1.x.x)                                 │
│  配置: .env.production                                      │
│  部署: 自动 (git tag)                                       │
│  域名: mirothinker.sam-ding.com                             │
└─────────────────────────────────────────────────────────────┘
```

## 日常开发流程

### 1. 创建功能分支

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### 2. 开发和测试

```bash
# 配置本地环境
cp .env.development .env
# 编辑 .env 填入 API 密钥

# 安装依赖
pip install -r backend/requirements.txt

# 运行开发服务器
cd backend
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# 运行测试
cd ..
pytest backend/tests -v
```

### 3. 提交代码

```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### 4. 创建 Pull Request

在 GitHub 上创建 PR：`feature/your-feature-name` → `develop`

- 等待 CI 检查通过
- 等待代码审查
- 合并到 develop

### 5. 自动部署到 Staging

合并到 develop 后，GitHub Actions 会自动：
- 运行测试
- 构建产物
- 部署到 staging 服务器
- 运行健康检查

访问 staging 环境验证功能。

## 发布流程

### 1. 创建发布分支

```bash
git checkout develop
git checkout -b release/v1.8.0
```

### 2. 更新版本号和 CHANGELOG

编辑 `backend/src/core/config.py`:
```python
APP_VERSION: str = "1.8.0"
```

更新 `CHANGELOG.md` 记录所有变更。

### 3. 测试 Release Candidate

Staging 环境会自动部署，进行手动测试验证。

### 4. 发布到生产环境

```bash
git checkout main
git merge --no-ff release/v1.8.0
git tag -a v1.8.0 -m "Release v1.8.0"
git push origin main --tags
```

GitHub Actions 会自动：
- 运行测试
- 构建产物
- 部署到生产服务器
- 运行健康检查
- 创建 GitHub Release

### 5. 同步回 develop

```bash
git checkout develop
git merge --no-ff release/v1.8.0
git push origin develop
```

### 6. 删除发布分支

```bash
git branch -d release/v1.8.0
git push origin --delete release/v1.8.0
```

## 部署命令

### 使用部署脚本

```bash
# 部署到 staging
./scripts/deploy-to-ecs.sh deploy staging

# 部署到 production
./scripts/deploy-to-ecs.sh deploy production

# 查看状态
./scripts/deploy-to-ecs.sh status staging

# 查看日志（最后 100 行）
./scripts/deploy-to-ecs.sh logs staging 100

# 重启服务
./scripts/deploy-to-ecs.sh restart staging

# 创建备份
./scripts/deploy-to-ecs.sh backup production

# 回滚到上一版本
./scripts/deploy-to-ecs.sh rollback production
```

### 手动部署

```bash
# SSH 到服务器
ssh root@47.108.141.189

# 检查服务状态
systemctl status mirothinker

# 查看日志
journalctl -u mirothinker -f

# 重启服务
systemctl restart mirothinker

# 健康检查
curl http://localhost:8001/api/health
```

## Git 分支策略

```
main (production) ────────────────────────────────●──────
                                                   ↑
                                                v1.8.0 tag
                                                  ↓
develop (staging) ───────●────────────────────────●──────
                        ↑                          ↑
                   feature PR                release merge
                     ↓
feature/new ───●────●─────────────────────────────────────
```

### 分支命名规范

| 分支类型 | 命名格式 | 示例 |
|---------|---------|------|
| 功能分支 | `feature/<name>` | `feature/new-research-module` |
| 发布分支 | `release/v<version>` | `release/v1.8.0` |
| 热修复分支 | `hotfix/<name>` | `hotfix/critical-bug` |

### 提交信息规范

```
<type>[optional scope]: <description>

feat: add quality enhancement module
fix: resolve call_llm response validation error
docs: update deployment guide
refactor: simplify agent state management
perf: optimize context window token usage
test: add unit tests for detect_domain
chore: update dependencies
```

## 配置文件说明

| 文件 | 用途 | 是否提交 |
|------|------|---------|
| `.env.development` | 本地开发配置 | ✅ 是（占位符） |
| `.env.staging` | 预发布环境配置 | ✅ 是（占位符） |
| `.env.production` | 生产环境配置 | ✅ 是（包含密钥）⚠️ |
| `.env` | 当前运行的配置 | ❌ 否（在 .gitignore） |
| `.miro/config.json` | 服务器连接信息 | ❌ 否（在 .gitignore） |
| `.miro/config.json.example` | 配置示例 | ✅ 是 |

⚠️ **注意**: `.env.production` 包含真实 API 密钥，请谨慎处理。

## 测试命令

```bash
# 运行所有测试
pytest backend/tests -v

# 运行特定测试文件
pytest backend/tests/test_agent.py -v

# 运行带覆盖率报告
pytest backend/tests --cov=backend/src --cov-report=html

# 运行特定测试类
pytest backend/tests/test_agent.py::TestDetectDomain -v

# 运行特定测试方法
pytest backend/tests/test_agent.py::TestDetectDomain::test_detect_tech -v
```

## 环境变量

### 必需变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `DASHSCOPE_API_KEY` | 百炼平台 API 密钥 | `sk-8aac4aac...` |
| `DASHSCOPE_BASE_URL` | API 基础 URL | `https://dashscope...` |
| `PORT` | 服务端口 | `8001` |

### 可选变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LARK_APP_ID` | 飞书应用 ID | `""` |
| `LARK_APP_SECRET` | 飞书应用密钥 | `""` |
| `MAX_CONCURRENT_TASKS` | 最大并发任务数 | `2` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 常见问题

### Q: 如何切换环境？

```bash
# 开发环境
cp .env.development .env

# Staging 配置
cp .env.staging .env

# Production 配置
cp .env.production .env
```

### Q: 部署失败怎么办？

```bash
# 查看部署日志
./scripts/deploy-to-ecs.sh logs production 200

# 回滚到上一版本
./scripts/deploy-to-ecs.sh rollback production
```

### Q: 如何查看服务状态？

```bash
# 本地开发
curl http://localhost:8000/api/health

# Staging
curl https://staging.mirothinker.sam-ding.com/api/health

# Production
curl https://mirothinker.sam-ding.com/api/health
```

### Q: API 密钥在哪里配置？

1. 本地开发：编辑 `.env` 文件，复制 `.env.development` 并填入真实密钥
2. Staging：GitHub Secrets 中配置 `STAGING_*` 变量
3. Production：GitHub Secrets 中配置 `PRODUCTION_*` 变量

## 监控和告警

### 健康检查

```bash
# 检查服务健康状态
curl http://localhost:8001/api/health

# 检查系统状态
curl http://localhost:8001/api/status
```

### 日志查看

```bash
# 实时日志
journalctl -u mirothinker -f

# 最近 100 条日志
journalctl -u mirothinker -n 100 --no-pager

# 搜索错误日志
journalctl -u mirothinker --grep="ERROR" --no-pager
```

### 资源监控

```bash
# CPU 和内存使用
top -p $(pgrep -f "uvicorn" | tr '\n' ',' | sed 's/,$//')

# 磁盘使用
du -sh /opt/mirothinker
df -h
```

## 备份和恢复

### 自动备份

每次部署前会自动备份到 `/opt/mirothinker/backups/`，保留最近 5 个版本。

### 手动备份

```bash
./scripts/deploy-to-ecs.sh backup production
```

### 恢复备份

```bash
# SSH 到服务器
ssh root@47.108.141.189

# 列出备份
ls -lh /opt/mirothinker/backups/

# 恢复
cd /opt/mirothinker
rm -rf backend
cp -r backups/backend.backup.YYYYMMDDHHMMSS backend
systemctl restart mirothinker
```

---

**更多详细信息请参考**:
- [DEPLOY.md](DEPLOY.md) - 完整部署指南
- [BRANCHING.md](BRANCHING.md) - Git 分支策略
- [CHANGELOG.md](CHANGELOG.md) - 版本历史
