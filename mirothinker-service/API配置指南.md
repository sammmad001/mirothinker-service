# API Key 配置指南

> MiroThinker 依赖的外部服务配置说明

---

## 一、Serper API Key (Google 搜索)

### 什么是 Serper?

Serper 是 Google Search 的 API 封装服务，让程序可以调用 Google 搜索结果。
MiroThinker 用它来搜索网络信息、查找资料。

### 获取步骤 (2 分钟)

#### 1. 注册账号

1. 访问: **https://serper.dev/**
2. 点击右上角 **"Sign Up"**
3. 使用邮箱注册 (或用 Google/GitHub 账号登录)
4. 验证邮箱

#### 2. 获取 API Key

1. 登录后，进入 **Dashboard** (控制台)
2. 在首页就能看到 **"API Key"** 区域
3. 复制你的 API Key (格式类似: `a1b2c3d4e5f6...`)

#### 3. 免费额度

| 套餐 | 价格 | 搜索次数 |
|------|------|---------|
| **Free** | $0 | 2,500 次/月 |
| Startup | $50/月 | 10,000 次/月 |
| Pro | $150/月 | 50,000 次/月 |

**免费额度足够测试使用！**

#### 4. 配置到 MiroThinker

编辑 `.env` 文件:
```bash
nano /Users/sam/Desktop/mirothinker-service/.env
```

填入:
```env
SERPER_API_KEY=你的serper密钥
```

---

## 二、Jina API Key (网页内容抓取)

### 什么是 Jina?

Jina Reader 是一个网页内容提取服务，能把网页转换成干净的 Markdown 格式。
MiroThinker 用它来抓取搜索结果的详细内容。

### 获取步骤 (2 分钟)

#### 1. 注册账号

1. 访问: **https://jina.ai/reader**
2. 点击 **"Get API Key"** 或 **"Sign Up"**
3. 使用邮箱注册

#### 2. 获取 API Key

1. 登录后进入 Dashboard
2. 找到 API Key 部分
3. 复制你的 Key (格式: `jina_xxxxxxxxxx...`)

#### 3. 免费额度

| 套餐 | 价格 | 调用次数 |
|------|------|---------|
| **Free** | $0 | 1,000 次/月 |
| Team | $99/月 | 10,000 次/月 |

**免费额度足够测试使用！**

#### 4. 替代方案 (可选)

如果不想注册 Jina，可以用以下替代:

| 服务 | 网址 | 免费额度 | 说明 |
|------|------|---------|------|
| **Firecrawl** | firecrawl.dev | 500 次/月 | 类似功能 |
| ** ScrapingBee** | scrapingbee.com | 1,000 次/月 | 网页抓取 |

#### 5. 配置到 MiroThinker

编辑 `.env` 文件:
```bash
nano /Users/sam/Desktop/mirothinker-service/.env
```

填入:
```env
JINA_API_KEY=jina_你的密钥
```

---

## 三、完整配置示例

### .env 文件完整内容

```env
# === 百炼 API (必需) ===
DASHSCOPE_API_KEY=sk-sp-djI.你的完整密钥

# === Serper 搜索 (必需) ===
SERPER_API_KEY=a1b2c3d4e5f6g7h8i9j0

# === Jina 网页抓取 (必需) ===
JINA_API_KEY=jina_xxxxxxxxxxxxxxxxxx
```

### 验证配置

```bash
# 重启服务
cd /Users/sam/Desktop/mirothinker-service
/Users/sam/Library/Python/3.9/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 1

# 检查配置
curl http://127.0.0.1:8000/api/health
```

**应返回**:
```json
{
  "status": "healthy",
  "dashscope_configured": true,
  "serper_configured": true,
  "jina_configured": true,
  "concurrency": {"max": 2, "available": 2, "locked": false}
}
```

三个 `true` 表示配置成功！

---

## 四、成本预估

### 单次研究任务消耗

| 服务 | 调用次数 | 单价 | 成本 |
|------|---------|------|------|
| Serper 搜索 | 20-30 次 | $0.005/次 | $0.10-0.15 |
| Jina 抓取 | 15-20 次 | $0.01/次 | $0.15-0.20 |
| 百炼 LLM | ~200K tokens | ¥0.08/千 | ¥16 |
| **总计** | - | - | **~¥17 ($0.25)** |

### 免费额度支持次数

| 服务 | 免费额度 | 单次消耗 | 可支持次数 |
|------|---------|---------|-----------|
| Serper (Free) | 2,500 次/月 | 25 次 | **100 次/月** |
| Jina (Free) | 1,000 次/月 | 18 次 | **55 次/月** |
| 百炼 Token Plan | 100K Credits | ~1,800 Credits | **55 次/月** |

**结论**: 免费额度足够前期测试和使用！

---

## 五、快速配置命令

```bash
# 1. 编辑配置
nano /Users/sam/Desktop/mirothinker-service/.env

# 2. 填入三个 API Key (从上面获取)
# DASHSCOPE_API_KEY=sk-xxxxx
# SERPER_API_KEY=xxxxx  
# JINA_API_KEY=jina_xxxxx

# 3. 保存并重启服务
# (Ctrl+X 保存 nano, 然后重启)
pkill -f uvicorn
cd /Users/sam/Desktop/mirothinker-service
/Users/sam/Library/Python/3.9/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 1

# 4. 验证
curl http://127.0.0.1:8000/api/health
```

---

*配置完成后，MiroThinker 就能执行完整的搜索研究了！*
