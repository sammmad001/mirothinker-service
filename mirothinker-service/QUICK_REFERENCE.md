# MiroThinker 快速参考

## 🚨 重要：部署路径

| 路径 | 状态 | 说明 |
|------|------|------|
| `/opt/mirothinker/` | ✅ 正确 | 服务实际运行目录 |
| `/root/mirothinker-service/` | ❌ 错误 | 不要部署到这里！ |

## 📦 部署命令

```bash
# 完整部署（推荐）
make deploy

# 仅部署后端
make deploy-backend

# 仅部署前端
make deploy-frontend

# 重启服务
make restart
```

## ✅ 部署前后验证

```bash
# 部署前：验证配置
make verify

# 部署后：检查状态
make check

# 查看日志
make logs
```

##  配置文件

`.miro/config.json` - 包含所有环境的正确路径

```json
{
  "production": {
    "deploy_dir": "/opt/mirothinker",
    "service_name": "mirothinker"
  }
}
```

## 🔍 故障排查

### 问题：部署后代码没有生效

1. 检查服务实际运行目录：
   ```bash
   ssh root@47.93.253.208 "ps aux | grep mirothinker"
   ```

2. 验证文件是否在服务目录下：
   ```bash
   ssh root@47.93.253.208 "ls -la /opt/mirothinker/frontend/js/"
   ```

3. 重启服务：
   ```bash
   make restart
   ```

### 问题：静态文件返回旧版本

1. 清除 Python 缓存：
   ```bash
   ssh root@47.93.253.208 "find /opt/mirothinker -name '*.pyc' -delete"
   ```

2. 重启服务：
   ```bash
   make restart
   ```

3. 浏览器强制刷新：Ctrl+Shift+R

## 📝 开发流程

1. **本地开发** → 在 `/Users/sam/Desktop/mirothinker-service/` 修改代码
2. **运行测试** → `make test`
3. **验证配置** → `make verify`
4. **部署代码** → `make deploy`
5. **验证部署** → `make check`

## ⚠️ 禁止操作

- ❌ 不要手动 `scp` 单个文件
- ❌ 不要直接修改服务器上的文件
- ❌ 不要部署到 `/root/` 目录
- ❌ 不要在未验证的情况下重启服务
