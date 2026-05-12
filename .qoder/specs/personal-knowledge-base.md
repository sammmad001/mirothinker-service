# PKB - 个人知识库系统
## 需求与技术规格文档

---

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-04-18 |
| 文档状态 | 草稿 |
| 负责人员 | - |

---

## 目录

1. [概述](#1-概述)
2. [需求规格](#2-需求规格)
3. [系统架构](#3-系统架构)
4. [技术规格](#4-技术规格)
5. [数据规格](#5-数据规格)
6. [AI能力规格](#6-ai能力规格)
7. [存储与备份](#7-存储与备份)
8. [安全与隐私](#8-安全与隐私)
9. [运维规格](#9-运维规格)
10. [长期可维护性](#10-长期可维护性)
11. [附录](#11-附录)

---

## 1. 概述

### 1.1 项目背景

在信息爆炸的时代，个人每天产生大量的思考、想法、学习成果和决策记录。传统工具（笔记软件、文档系统）存在以下核心问题：

| 问题 | 描述 | 影响 |
|------|------|------|
| 知识孤岛 | 信息分散在多个平台，无法关联 | 知识利用率低 |
| 一次性答案 | 每次提问都需重新检索、分析 | 重复劳动 |
| 维护成本高 | 需要人工整理、归类、更新 | 难以坚持 |
| 技术依赖 | 商业服务可能停止，数据可能被锁定 | 长期风险 |

### 1.2 项目目标

本项目旨在构建一套**个人知识库系统 (Personal Knowledge Base, PKB)**，实现以下核心目标：

1. **知识持续沉淀**：不是一次性问答，而是让知识随着时间不断积累、结构化
2. **多端便捷输入**：通过飞书、CLI等工具随时随地记录
3. **长期稳定存储**：不受技术迭代影响，10年以上可用
4. **智能分析能力**：AI辅助理解和关联，发现隐藏的知识连接

### 1.3 设计理念：LLM Wiki

本系统借鉴 Andrej Karpathy 提出的 **LLM Wiki** 理念，重新定义 AI 在知识管理中的角色：

> 传统模式：LLM 作为"问答器" → 提问时临时检索 → 一次性答案
>
> LLM Wiki 模式：LLM 作为"Wiki维护者" → 平时持续维护 → 可积累的结构化资产

**核心转变**：让 LLM 承担低创造性、高维护成本的工作（整理、归档、链接、更新），人类专注于判断什么重要。

### 1.4 术语定义

| 术语 | 定义 |
|------|------|
| PKB | Personal Knowledge Base，个人知识库系统 |
| Raw Layer | 原始资料层，存放未经处理的原始内容 |
| Wiki Layer | Wiki层，由LLM维护的结构化知识页面 |
| Schema Layer | 规则层，定义LLM维护行为的约束规则 |
| Ingest | 资料摄取流程，新资料进入系统并被处理 |
| Lint | 周期性巡检，发现和维护Wiki质量 |
| Entity | 实体，知识图谱中的节点（人、项目、概念等） |
| Memory | 记忆，用户记录的想法、思考、成果 |

---

## 2. 需求规格

### 2.1 功能需求

#### 2.1.1 输入系统

| 功能 | 描述 | 优先级 | 备注 |
|------|------|--------|------|
| F-001 | 飞书机器人接收消息 | P0 | 私聊/指令模式 |
| F-002 | CLI工具命令行输入 | P0 | pkb add/search/list/sync |
| F-003 | Web界面文件上传 | P1 | PDF/DOCX/MD/TXT |
| F-004 | 消息格式解析 | P0 | 支持文本/图片/文件 |
| F-005 | 指令识别 | P0 | #note, #search, #tag等 |

#### 2.1.2 存储系统

| 功能 | 描述 | 优先级 | 备注 |
|------|------|--------|------|
| F-010 | 原始资料存储 | P0 | 存入raw/目录 |
| F-011 | Wiki页面管理 | P0 | 创建/更新/删除 |
| F-012 | 向量索引 | P0 | ChromaDB |
| F-013 | 元数据管理 | P0 | SQLite |
| F-014 | 版本历史 | P1 | 文档变更记录 |

#### 2.1.3 AI处理

| 功能 | 描述 | 优先级 | 备注 |
|------|------|--------|------|
| F-020 | 资料自动分析 | P0 | LLM理解新资料内容 |
| F-021 | Wiki页面自动生成 | P0 | sources/topics/entities页 |
| F-022 | 交叉链接补全 | P0 | 自动关联相关页面 |
| F-023 | 语义搜索 | P0 | 基于Wiki层回答 |
| F-024 | 自动摘要生成 | P1 | AI生成内容摘要 |
| F-025 | 标签推荐 | P1 | AI推荐合适标签 |
| F-026 | 实体识别 | P1 | NER抽取实体 |
| F-027 | 周期性Lint | P1 | 质量巡检 |

#### 2.1.4 知识管理

| 功能 | 描述 | 优先级 | 备注 |
|------|------|--------|------|
| F-030 | 知识图谱构建 | P2 | 实体关系可视化 |
| F-031 | 决策记录 | P1 | 架构决策、结论记录 |
| F-032 | 项目页面 | P1 | 项目跟踪 |
| F-033 | 知识回写 | P1 | 有价值回答自动沉淀 |

### 2.2 非功能需求

#### 2.2.1 性能

> **设计原则**：个人知识库以**质量优先**，非高并发场景，性能指标应贴合实际使用模式。

| 指标 | 要求 | 场景分类 | 说明 |
|------|------|----------|------|
| **搜索响应时间** | | | |
| ├ 关键词搜索 | < 100ms | SQLite FTS | 纯文本匹配 |
| ├ 向量检索 | < 500ms | ChromaDB top-5 | 语义搜索 |
| └ LLM 综合回答 | 1-5s | 含模型推理 | 本地 Ollama 500ms-2s，云端 1-3s |
| **并发能力** | | | |
| ├ 日常使用 | 1-2 QPS | 单人交互 | 个人场景足够 |
| ├ 后台处理 | 串行执行 | Ingest/Lint | 避免资源竞争 |
| └ 峰值容忍 | 5 QPS / 30s | 批量导入 | 短时间突发 |
| **启动时间** | | | |
| ├ 服务冷启动 | < 10s | FastAPI + DB 初始化 | 首次加载模型除外 |
| └ Ollama 模型加载 | 5-15s | 首次推理请求 | 模型驻留后无延迟 |
| **索引速度** | | | |
| ├ 单条 Ingest | 1-3s | 含 embedding + LLM 分析 | 异步处理 |
| ├ 批量导入 | 50-100条/分钟 | 后台队列 | 取决于 embedding 模型 |
| └ Lint 巡检 | 10页/分钟 | 质量检查 | 本地模型 |

**性能优化策略**：
1. **异步处理**：Ingest Pipeline 使用后台队列，不阻塞用户输入
2. **缓存机制**：热门搜索结果缓存 5 分钟，避免重复 embedding 计算
3. **模型驻留**：Ollama 模型加载后保持内存，避免重复加载延迟
4. **并发限制**：使用 Semaphore 限制同时 LLM 请求数（建议 2），防止 OOM

#### 2.2.2 可用性

| 指标 | 要求 | 说明 |
|------|------|------|
| 系统可用性 | 99.5% | 核心功能 |
| 故障恢复 | < 30分钟 | 数据恢复 |
| 备份频率 | 每日增量 | 自动备份 |

#### 2.2.3 可维护性

| 指标 | 要求 | 说明 |
|------|------|------|
| 代码可读性 | 高 | 完整注释、文档 |
| 测试覆盖 | > 80% | 核心模块 |
| 部署方式 | Docker | 一键部署 |

#### 2.2.4 长期稳定性

| 指标 | 要求 | 说明 |
|------|------|------|
| 数据格式 | 开放标准 | Markdown/SQLite |
| 迁移能力 | 每年验证 | 完整导出 |
| 供应商锁定 | 最小化 | 开源优先 |

### 2.3 用户角色与场景

#### 2.3.1 用户角色

| 角色 | 描述 | 主要操作 |
|------|------|----------|
| 记录者 | 通过飞书/CLI快速记录 | add, tag |
| 询问者 | 查询和分析已有知识 | search, query |
| 维护者 | AI自动维护Wiki | ingest, lint |
| 审计者 | 检查系统状态和数据 | status, backup |

#### 2.3.2 典型场景

**场景1：快速记录**
```
用户 → 飞书私聊 → "#note 今天学到了关于向量数据库的新知识"
→ 系统存入raw/inbox → LLM分析 → 更新wiki/topics/AI相关页
→ 补全交叉链接 → 追加log.md
```

**场景2：知识检索**
```
用户 → 飞书 → "#search 我在项目X中学到了哪些架构原则"
→ 读取index.md和相关Wiki页 → LLM综合回答
→ 如有必要，回写成新Wiki页
```

**场景3：定期巡检**
```
系统 → 每周执行Lint → 检测孤儿页、重复、过期
→ 标记问题 → 更新相关页 → 记录log.md
```

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PKB 系统架构图                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌────────────────────────────────────────────────────────────────┐   │
│    │                         用户层                                  │   │
│    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│    │  │  飞书   │  │  CLI    │  │  Web    │  │  定时   │           │   │
│    │  │ 机器人  │  │  工具   │  │  界面   │  │  任务   │           │   │
│    │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │   │
│    └───────┼───────────┼───────────┼───────────┼─────────────────┘   │
│            └───────────┴───────────┴───────────┘                       │
│                              │                                          │
│                              ▼                                          │
│    ┌────────────────────────────────────────────────────────────────┐   │
│    │                       API 网关层                                │   │
│    │                    FastAPI (异步)                               │   │
│    │    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │
│    │    │  消息    │  │  文档    │  │  搜索    │  │  系统    │      │   │
│    │    │  路由    │  │  路由    │  │  路由    │  │  路由    │      │   │
│    │    └──────────┘  └──────────┘  └──────────┘  └──────────┘      │   │
│    └────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│            ┌─────────────────┼─────────────────┐                        │
│            │                 │                 │                        │
│            ▼                 ▼                 ▼                        │
│    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐              │
│    │   Ingest      │ │    Query      │ │     Lint      │              │
│    │   Pipeline    │ │   Pipeline    │ │   Pipeline    │              │
│    │               │ │               │ │               │              │
│    │ 1. 解析       │ │ 1. 读Wiki    │ │ 1. 孤儿页    │              │
│    │ 2. 向量化     │ │ 2. 检索      │ │ 2. 重复页    │              │
│    │ 3. LLM分析    │ │ 3. 综合      │ │ 3. 过期标记  │              │
│    │ 4. 建页       │ │ 4. 回写      │ │ 4. 链接补全  │              │
│    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘              │
│            └─────────────────┼─────────────────┘                        │
│                              │                                          │
│                              ▼                                          │
│    ┌────────────────────────────────────────────────────────────────┐   │
│    │                        存储层                                    │   │
│    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │   │
│    │  │ SQLite   │  │ ChromaDB │  │ 文件系统 │  │  配置    │        │   │
│    │  │ 元数据   │  │ 向量库   │  │ 原始文件 │  │  (YAML)  │        │   │
│    │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │   │
│    └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 三层架构

PKB 采用经典的三层分离架构，确保职责清晰、易于维护：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         三层架构详图                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ╔═══════════════════════════════════════════════════════════════════╗ │
│   ║                     第三层：Schema Layer                           ║ │
│   ║                   (规则约束，决定系统上限)                          ║ │
│   ╠═══════════════════════════════════════════════════════════════════╣ │
│   ║                                                                   ║ │
│   ║   AGENTS.md                                                       ║ │
│   ║   ├── 目录规则     │ 哪些是raw，哪些是wiki                        ║ │
│   ║   ├── Ingest规则  │ 新资料处理流程                                ║ │
│   ║   ├── Query规则   │ 回答问题前做什么                              ║ │
│   ║   ├── Lint规则    │ 巡检哪些问题                                  ║ │
│   ║   ├── 页面规范    │ 每类页面的字段要求                            ║ │
│   ║   └── 日志规范    │ 如何记录操作                                  ║ │
│   ║                                                                   ║ │
│   ║   CONFIG/                                                        ║ │
│   ║   ├── page_templates/    # 页面模板                               ║ │
│   ║   ├── entity_types.yaml # 实体类型定义                           ║ │
│   ║   └── tag_hierarchy.yaml# 标签层级                               ║ │
│   ║                                                                   ║ │
│   ╚═══════════════════════════════════════════════════════════════════╝ │
│                                    │                                    │
│                                    ▼                                    │
│   ╔═══════════════════════════════════════════════════════════════════╗ │
│   ║                      第二层：Wiki Layer                            ║ │
│   ║                   (LLM维护，完全可编辑)                           ║ │
│   ╠═══════════════════════════════════════════════════════════════════╣ │
│   ║                                                                   ║ │
│   ║   wiki/                                                           ║ │
│   ║   ├── index.md          # 知识库总览，更新频率最高                 ║ │
│   ║   ├── log.md           # 操作日志，所有变更记录                   ║ │
│   ║   │                                                               ║ │
│   ║   ├── sources/         # 资料索引页                               ║ │
│   ║   │   ├── 2026-04-18-xxxx-飞书消息.md                           ║ │
│   ║   │   └── 2026-04-17-xxxx-项目文档.md                           ║ │
│   ║   │                                                               ║ │
│   ║   ├── topics/          # 主题深度页                                ║ │
│   ║   │   ├── AI与机器学习.md                                        ║ │
│   ║   │   ├── Python编程.md                                          ║ │
│   ║   │   └── 系统架构.md                                            ║ │
│   ║   │                                                               ║ │
│   ║   ├── entities/        # 实体页                                    ║ │
│   ║   │   ├── PKB项目.md                                            ║ │
│   ║   │   ├── Sam.md                                                ║ │
│   ║   │   └── Ollama.md                                             ║ │
│   ║   │                                                               ║ │
│   ║   ├── projects/        # 项目页                                    ║ │
│   ║   │   └── personal-website.md                                    ║ │
│   ║   │                                                               ║ │
│   ║   └── decisions/       # 决策记录                                  ║ │
│   ║       ├── 2026-04-使用Ollama本地推理.md                           ║ │
│   ║       └── 2026-03-存储方案决策.md                                 ║ │
│   ║                                                                   ║ │
│   ╚═══════════════════════════════════════════════════════════════════╝ │
│                                    │                                    │
│                                    ▼                                    │
│   ╔═══════════════════════════════════════════════════════════════════╗ │
│   ║                    第一层：Raw Layer                               ║ │
│   ║                  (source of truth，LLM不可修改)                    ║ │
│   ╠═══════════════════════════════════════════════════════════════════╣ │
│   ║                                                                   ║ │
│   ║   raw/                                                            ║ │
│   ║   ├── inbox/           # 新进入的原始资料                          ║ │
│   ║   │   ├── 2026-04-18-message-001.md                              ║ │
│   ║   │   ├── 2026-04-18-message-002.md                              ║ │
│   ║   │   └── 2026-04-17-file-001.pdf                                ║ │
│   ║   │                                                               ║ │
│   ║   ├── notes/          # 日常随手记                                ║ │
│   ║   │   └── 2026/04/                                                 ║ │
│   ║   │                                                               ║ │
│   ║   ├── documents/      # 上传的文档                                ║ │
│   ║   │   └── 2026/                                                      ║ │
│   ║   │                                                               ║ │
│   ║   ├── feishu/         # 飞书消息归档                              ║ │
│   ║   │   └── 2026/04/                                                  ║ │
│   ║   │                                                               ║ │
│   ║   └── repos/          # 代码仓库                                  ║ │
│   ║       └── example-project/                                        ║ │
│   ║                                                                   ║ │
│   ╚═══════════════════════════════════════════════════════════════════╝ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 模块设计

#### 3.3.1 输入模块

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           输入模块                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     飞书机器人模块                                │   │
│   │                                                                   │   │
│   │   lark-oapi SDK                                                  │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   Event Handler                                                  │   │
│   │       │                                                          │   │
│   │       ├── 消息接收 (im.message.receive_v1)                       │   │
│   │       ├── 指令解析 (#note, #search, #tag, #help)                 │   │
│   │       ├── 内容提取 (text/image/file)                            │   │
│   │       └── 回复生成                                               │   │
│   │                                                                   │   │
│   │   Commands:                                                      │   │
│   │   - #note <content>     添加笔记                                 │   │
│   │   - #search <query>     搜索知识库                               │   │
│   │   - #tag <tags>         添加标签                                 │   │
│   │   - #link <id1> <id2>   关联页面                                 │   │
│   │   - #help               显示帮助                                 │   │
│   │   - #status             系统状态                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      CLI 工具模块                                │   │
│   │                                                                   │   │
│   │   Typer + Rich                                                   │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   Commands:                                                      │   │
│   │   ├── pkb add <content>          快速添加                       │   │
│   │   ├── pkb add --file <path>       添加文件                       │   │
│   │   ├── pkb add --url <url>         添加网页                       │   │
│   │   ├── pkb search <query>          搜索                           │   │
│   │   ├── pkb list [--tag <tag>]      列出笔记                       │   │
│   │   ├── pkb get <id>               查看单条                       │   │
│   │   ├── pkb edit <id>              编辑                           │   │
│   │   ├── pkb tag <id> <tags>        标签管理                       │   │
│   │   ├── pkb sync                   同步                           │   │
│   │   ├── pkb backup                 备份                           │   │
│   │   ├── pkb lint                   巡检                           │   │
│   │   └── pkb status                 状态                           │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 处理模块

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           处理模块                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     Ingest Pipeline                              │   │
│   │                                                                   │   │
│   │   输入: 原始资料 (text/file/url)                                  │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 解析器  │  TextParser / FileParser / URLParser               │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 存储    │  → raw/inbox/ + SQLite (元数据)                  │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 向量化  │  → ChromaDB (embedding)                           │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ LLM分析 │  Ollama/GPT                                        │   │
│   │   │         │  - 理解内容                                        │   │
│   │   │         │  - 提取关键信息                                    │   │
│   │   │         │  - 识别关联实体                                    │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ Wiki更新│  - 创建/更新 sources/ 页面                         │   │
│   │   │         │  - 更新 topics/entities/projects/                 │   │
│   │   │         │  - 补全交叉链接                                    │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 记录日志│  → log.md + audit_logs                            │   │
│   │   └─────────┘                                                    │   │
│   │                                                                   │   │
│   │   输出: Wiki页面更新 + 索引更新 + 日志记录                        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Query Pipeline                              │   │
│   │                                                                   │   │
│   │   输入: 用户查询                                                  │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 读取Wiki│  - index.md (定位)                                │   │
│   │   │         │  - 相关页面 (top-k)                                │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 意图识别│  - 分类: 检索/总结/分析/建议                       │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ Wiki搜索│  - 向量检索 (ChromaDB)                             │   │
│   │   │         │  - 关键词检索 (SQLite)                             │   │
│   │   │         │  - 知识图谱 (实体关联)                             │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 结果融合│  RRF (Reciprocal Rank Fusion)                     │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ LLM生成 │  - 综合Wiki内容回答                                │   │
│   │   │         │  - 引用来源链接                                    │   │
│   │   │         │  - 评估是否值得回写                                │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 回写判断│  if 回答有价值 → 创建新Wiki页                      │   │
│   │   └─────────┘                                                    │   │
│   │                                                                   │   │
│   │   输出: 回答 + 来源引用 + (可选)新Wiki页                          │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Lint Pipeline                              │   │
│   │                                                                   │   │
│   │   触发: 每周定时 / 手动触发                                       │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 孤儿页  │  扫描未被引用的页面 → 标记/合并/删除              │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 重复检测│  相似页面合并 → 保留最佳，标记重复                 │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 过期标记│  检测过时结论 → 更新/标记/移除                     │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 链接检查│  修复死链 → 补全缺失链接                          │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 概念提升│  高频提及但无页面 → 建议创建                       │   │
│   │   └────┬────┘                                                    │   │
│   │       │                                                          │   │
│   │       ▼                                                          │   │
│   │   ┌─────────┐                                                    │   │
│   │   │ 生成报告│  → log.md                                          │   │
│   │   └─────────┘                                                    │   │
│   │                                                                   │   │
│   │   输出: 巡检报告 + 建议操作                                       │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 技术规格

### 4.1 技术栈总览

| 层级 | 组件 | 选型 | 版本 | 说明 |
|------|------|------|------|------|
| **运行时** | Python | 3.11+ | - | 主语言 |
| **后端框架** | FastAPI | 0.109+ | 异步API | |
| **ORM** | SQLAlchemy | 2.0+ | 异步支持 | |
| **数据库** | SQLite | 3.45+ | 单文件 | 元数据存储 |
| **向量库** | ChromaDB | 0.4+ | 本地持久化 | 语义搜索 |
| **LLM框架** | Ollama + OpenAI | - | - | 混合推理 |
| **飞书SDK** | lark-oapi | 0.2+ | - | 官方SDK |
| **CLI框架** | Typer + Rich | - | - | 命令行工具 |
| **容器化** | Docker | 24+ | - | 部署 |
| **前端** | React + TypeScript | 18+/5+ | Vite构建 | Web界面 |

### 4.2 依赖管理

所有依赖通过 `pyproject.toml` 管理，版本锁定主版本号避免自动升级导致不兼容。

```toml
[project]
name = "pkb"
version = "0.1.0"
requires-python = ">=3.11"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = ">=0.109.0,<0.111.0"
uvicorn = {extras = ["standard"], version = ">=0.27.0,<0.29.0"}
sqlalchemy = {extras = ["asyncio"], version = ">=2.0.25,<2.1.0"}
aiosqlite = ">=0.19.0,<0.20.0"
chromadb = ">=0.4.22,<0.5.0"
openai = ">=1.12.0,<2.0.0"
lark-oapi = ">=0.2.8,<0.3.0"
typer = ">=0.9.0,<0.10.0"
rich = ">=13.7.0,<14.0.0"
httpx = ">=0.26.0,<0.27.0"
pydantic = ">=2.5.0,<3.0.0"
pydantic-settings = ">=2.1.0,<3.0.0"
python-dotenv = ">=1.0.0,<2.0.0"
```

### 4.3 项目结构

```
pkb/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 配置管理
│   │   ├── api/                    # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── messages.py         # 消息接口
│   │   │   ├── documents.py       # 文档接口
│   │   │   ├── search.py           # 搜索接口
│   │   │   └── system.py           # 系统接口
│   │   ├── core/                   # 核心模块
│   │   │   ├── database.py         # 数据库
│   │   │   ├── vector_store.py     # 向量存储
│   │   │   └── file_storage.py     # 文件存储
│   │   ├── models/                # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   ├── memory.py
│   │   │   ├── entity.py
│   │   │   ├── tag.py
│   │   │   └── wiki_page.py
│   │   ├── services/              # 业务服务
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py          # Ingest Pipeline
│   │   │   ├── query.py           # Query Pipeline
│   │   │   ├── lint.py            # Lint Pipeline
│   │   │   ├── embedding.py       # Embedding 服务
│   │   │   └── llm.py             # LLM 服务
│   │   ├── feishu/                # 飞书集成
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # 飞书客户端
│   │   │   ├── handlers.py        # 事件处理
│   │   │   └── commands.py        # 指令处理
│   │   └── utils/                 # 工具函数
│   │       ├── __init__.py
│   │       ├── markdown.py        # Markdown 处理
│   │       ├── hash.py            # 哈希计算
│   │       └── time.py            # 时间处理
│   └── tests/                     # 测试
│
├── cli/
│   ├── src/
│   │   └── pkb_cli/
│   │       ├── __init__.py
│   │       ├── main.py            # CLI 入口
│   │       ├── commands/          # 命令
│   │       │   ├── add.py
│   │       │   ├── search.py
│   │       │   ├── list.py
│   │       │   ├── sync.py
│   │       │   └── lint.py
│   │       └── api/               # API 客户端
│   │           └── client.py
│   └── pyproject.toml
│
├── data/                           # 数据目录 (运行时创建)
│   ├── raw/
│   ├── wiki/
│   ├── db/
│   │   └── pkb.db                 # SQLite 数据库
│   └── vectors/
│       └── chroma/                 # ChromaDB 存储
│
├── AGENTS.md                       # LLM Wiki 规则
├── CONFIG/
│   ├── page_templates/             # 页面模板
│   ├── entity_types.yaml          # 实体类型
│   └── tag_hierarchy.yaml         # 标签层级
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

### 4.4 API 接口规格

#### 4.4.1 消息接口

```
POST /api/v1/messages
---
接收飞书/CLI消息

Request:
{
    "source": "feishu" | "cli" | "web",
    "content_type": "text" | "image" | "file",
    "content": string,
    "metadata": {
        "user_id": string,
        "chat_id": string,
        "message_id": string
    }
}

Response:
{
    "success": true,
    "message_id": string,
    "action": "note_added" | "search_results" | "error",
    "data": {...}
}
```

#### 4.4.2 搜索接口

```
POST /api/v1/search
---
语义搜索

Request:
{
    "query": string,
    "mode": "wiki" | "raw" | "all",
    "top_k": int (default: 5),
    "include_sources": bool (default: true)
}

Response:
{
    "query": string,
    "results": [
        {
            "page_id": string,
            "title": string,
            "type": "wiki" | "raw",
            "content": string,
            "score": float,
            "source_ref": string,
            "related_pages": [string]
        }
    ],
    "answer": string (optional),
    "suggestions": [string]
}
```

#### 4.4.3 文档接口

```
POST /api/v1/documents
---
上传文档

GET /api/v1/documents
---
列出文档

GET /api/v1/documents/{id}
---
获取文档详情

DELETE /api/v1/documents/{id}
---
删除文档
```

#### 4.4.4 Wiki 接口

```
GET /api/v1/wiki/index
---
获取Wiki总览

GET /api/v1/wiki/pages
---
列出Wiki页面

GET /api/v1/wiki/pages/{type}/{slug}
---
获取特定页面

PUT /api/v1/wiki/pages/{id}
---
更新Wiki页面

GET /api/v1/wiki/graph
---
获取知识图谱数据
```

#### 4.4.5 系统接口

```
GET /api/v1/system/status
---
系统状态

POST /api/v1/system/lint
---
触发Lint巡检

POST /api/v1/system/backup
---
触发备份

GET /api/v1/system/logs
---
获取操作日志
```

---

## 5. 数据规格

### 5.1 SQLite 数据模型

#### 5.1.1 ER 图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           数据模型 ER 图                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐   │
│   │  Document   │         │   Memory     │         │   Entity     │   │
│   ├──────────────┤         ├──────────────┤         ├──────────────┤   │
│   │ id (PK)     │    ┌───│ id (PK)     │    ┌───│ id (PK)     │   │
│   │ title       │    │   │ type        │    │   │ name        │   │
│   │ content     │    │   │ content     │    │   │ type        │   │
│   │ content_hash│    │   │ doc_id (FK) │────┘   │ description │   │
│   │ source      │    │   │ parent_id   │        │ aliases     │   │
│   │ source_id   │    │   │ importance  │        │ properties   │   │
│   │ doc_type    │    │   │ mood        │        │ first_seen  │   │
│   │ file_path   │    │   │ created_at  │        │ last_seen   │   │
│   │ summary     │    │   └──────┬───────┘        └──────┬─────┘   │
│   │ vector_id   │    │          │                       │         │
│   │ status      │    │          │                       │         │
│   │ is_favorite │    │          │                       │         │
│   │ created_at  │    │          │                       │         │
│   └──────┬──────┘    │          │                       │         │
│          │            │          │                       │         │
│          │            │   ┌──────┴───────┐         ┌──────┴─────┐   │
│          │            │   │  MemoryTag   │         │ EntityRel  │   │
│          │            │   ├──────────────┤         ├────────────┤   │
│          │            │   │ memory_id(FK)│─────────│ src_id(FK) │   │
│          │            └───│ tag_id (FK)  │    ┌────│ dst_id(FK) │   │
│          │                └──────────────┘    │    │ rel_type   │   │
│          │                                    │    │ confidence │   │
│   ┌──────┴──────┐                            │    └────────────┘   │
│   │ DocumentTag │                            │                       │
│   ├──────────────┤                            │                       │
│   │ doc_id (FK) │─────────────────────────────┘                       │
│   │ tag_id (FK) │                                                       │
│   └──────────────┘                                                       │
│          │                                                                │
│          │         ┌──────────────┐        ┌──────────────┐            │
│          └────────│    Tag        │────────│  WikiPage    │            │
│                    ├──────────────┤        ├──────────────┤            │
│                    │ id (PK)     │        │ id (PK)      │            │
│                    │ name        │        │ path         │            │
│                    │ slug        │        │ wiki_type    │            │
│                    │ color       │        │ title        │            │
│                    │ parent_id   │        │ content      │            │
│                    │ level       │        │ doc_id (FK)  │            │
│                    │ usage_count │        │ created_at   │            │
│                    └──────────────┘        │ updated_at   │            │
│                                             └──────────────┘            │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        AuditLog                                 │   │
│   ├─────────────────────────────────────────────────────────────────┤   │
│   │ id | action | entity_type | entity_id | user_id | details | ts │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 5.1.2 表结构定义

```sql
-- 文档表
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT UNIQUE,
    source TEXT NOT NULL CHECK(source IN ('feishu', 'cli', 'web', 'file')),
    source_id TEXT,
    doc_type TEXT CHECK(doc_type IN ('note', 'doc', 'web', 'chat')),
    file_path TEXT,
    file_size INTEGER,
    language TEXT DEFAULT 'zh-CN',
    word_count INTEGER DEFAULT 0,
    summary TEXT,
    vector_id TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived', 'deleted')),
    is_favorite INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    deleted_at DATETIME,

    INDEX idx_source (source),
    INDEX idx_created (created_at),
    INDEX idx_status (status)
);

-- 记忆表
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('thought', 'idea', 'learn', 'todo', 'note', 'question')),
    content TEXT NOT NULL,
    embedding_id TEXT,
    parent_id TEXT REFERENCES memories(id),
    doc_id TEXT REFERENCES documents(id),
    importance INTEGER DEFAULT 3 CHECK(importance BETWEEN 1 AND 5),
    mood TEXT,
    language TEXT DEFAULT 'zh-CN',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    INDEX idx_type (type),
    INDEX idx_created (created_at),
    INDEX idx_parent (parent_id)
);

-- 实体表 (知识图谱)
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('person', 'project', 'concept', 'tool', 'location', 'event', 'organization')),
    description TEXT,
    aliases TEXT,  -- JSON array
    properties TEXT,  -- JSON object
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME,
    mention_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(name, type),
    INDEX idx_type (type),
    INDEX idx_name (name)
);

-- 实体关系表
CREATE TABLE entity_relations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES entities(id),
    target_id TEXT NOT NULL REFERENCES entities(id),
    relation_type TEXT NOT NULL CHECK(relation_type IN ('works_on', 'uses', 'similar_to', 'part_of', 'depends_on', 'related_to')),
    properties TEXT,  -- JSON object
    confidence REAL DEFAULT 1.0 CHECK(confidence BETWEEN 0 AND 1),
    source_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(source_id, target_id, relation_type),
    INDEX idx_source (source_id),
    INDEX idx_target (target_id)
);

-- Wiki页面表
CREATE TABLE wiki_pages (
    id TEXT PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    wiki_type TEXT NOT NULL CHECK(wiki_type IN ('sources', 'topics', 'entities', 'projects', 'decisions')),
    title TEXT NOT NULL,
    content TEXT,
    doc_id TEXT REFERENCES documents(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,

    INDEX idx_type (wiki_type),
    INDEX idx_path (path)
);

-- 标签表 (层级)
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#6B7280',
    icon TEXT,
    parent_id TEXT REFERENCES tags(id),
    level INTEGER DEFAULT 0,
    description TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_parent (parent_id),
    INDEX idx_slug (slug)
);

-- 文档-标签关联
CREATE TABLE document_tags (
    doc_id TEXT REFERENCES documents(id),
    tag_id TEXT REFERENCES tags(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (doc_id, tag_id)
);

-- 记忆-标签关联
CREATE TABLE memory_tags (
    memory_id TEXT REFERENCES memories(id),
    tag_id TEXT REFERENCES tags(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (memory_id, tag_id)
);

-- 审计日志
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL CHECK(action IN ('create', 'update', 'delete', 'tag', 'link', 'ingest', 'lint')),
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    user_id TEXT,
    old_value TEXT,  -- JSON
    new_value TEXT,  -- JSON
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at)
);
```

### 5.2 文件系统格式

#### 5.2.1 Wiki 页面格式

```markdown
---
id: wiki-uuid-xxx
type: topics
title: AI与机器学习
created_at: 2026-04-01T10:00:00Z
updated_at: 2026-04-18T14:30:00Z
tags: [AI, 机器学习, 技术]
related_pages:
  - wiki/topics/深度学习.md
  - wiki/entities/Ollama.md
  - wiki/decisions/2026-04-使用Ollama本地推理.md
source_ref:
  - raw/inbox/2026-04-01-message-001.md
  - raw/documents/2026-04-10-paper-ml-survey.pdf
---

# AI与机器学习

## 定义

人工智能（AI）是让机器具有人类智能的技术，机器学习（ML）是AI的一个子领域...

## 关键概念

- 监督学习
- 无监督学习
- 深度学习
- 强化学习

## 相关项目

- [[PKB项目]] - 知识库系统
- personal-website - 个人网站

## 最近的认知

> 2026-04-15: 认识到本地推理的重要性，云端API有隐私和成本问题

## 待探索

- [ ] Transformer架构深入研究
- [ ] 多模态模型
```

#### 5.2.2 实体页面格式

```markdown
---
id: entity-uuid-xxx
type: entities
entity_type: tool
name: Ollama
created_at: 2026-03-15T09:00:00Z
updated_at: 2026-04-18T10:00:00Z
tags: [LLM, 本地推理, 工具]
aliases: ["ollama", "Ollama AI"]
properties:
  github: https://github.com/ollama/ollama
  models: ["qwen2.5", "llama3", "mistral", "nomic-embed-text"]
  platform: macOS, Linux, Windows
related_pages:
  - wiki/decisions/2026-04-使用Ollama本地推理.md
  - wiki/topics/AI与机器学习.md
source_ref:
  - raw/inbox/2026-03-15-ollama-intro.md
---

# Ollama

## 简介

Ollama 是一个本地大语言模型运行平台，支持在个人设备上运行各种开源LLM...

## 使用场景

- 本地知识库推理
- 开发测试
- 隐私敏感场景

## 相关决策

- [[2026-04-使用Ollama本地推理]] - 选择Ollama作为主力推理引擎
```

---

## 6. AI能力规格

### 6.1 LLM 架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LLM 混合架构                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    日常任务：本地 Ollama                         │   │
│   │                                                                   │   │
│   │   模型: Qwen2.5-7B-Instruct (量化版)                             │   │
│   │   显存需求: ~4GB                                                  │   │
│   │   适用:                                                           │   │
│   │   - 笔记摘要生成                                                   │   │
│   │   - 标签推荐                                                      │   │
│   │   - 页面内容分析                                                  │   │
│   │   - 实体识别                                                      │   │
│   │   - Lint 巡检                                                    │   │
│   │                                                                   │   │
│   │   成本: $0 (离线运行)                                            │   │
│   │   延迟: 500ms-2s (本地)                                          │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    复杂任务：云端 API                            │   │
│   │                                                                   │   │
│   │   主选: GPT-4o-mini                                              │   │
│   │   备选: Claude 3.5 Haiku                                         │   │
│   │                                                                   │   │
│   │   适用:                                                           │   │
│   │   - 多文档综合分析                                                │   │
│   │   - 复杂推理回答                                                  │   │
│   │   - 知识图谱构建                                                  │   │
│   │   - 关键决策建议                                                  │   │
│   │                                                                   │   │
│   │   成本: ~$0.15/1M tokens (GPT-4o-mini)                          │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Embedding 配置

| 参数 | 值 | 说明 |
|------|-----|------|
| 模型 | text-embedding-3-small | OpenAI (1536维) |
| 备选 | nomic-embed-text | Ollama 本地 |
| chunk_size | 500 tokens | 单块大小 |
| chunk_overlap | 50 tokens | 块重叠 |
| batch_size | 100 | 批量处理 |

### 6.3 Ingest Prompt 模板

```markdown
# Ingest 分析 Prompt

你是一个知识库维护者，负责将新资料整合到Wiki中。

## 原始资料
{raw_content}

## 已有上下文
- 相关主题: {related_topics}
- 相关实体: {related_entities}
- 最近更新: {recent_updates}

## 你的任务

1. **理解内容**: 总结这段资料的核心要点
2. **提取实体**: 识别人名、项目名、工具名、概念等
3. **关联分析**: 找出与现有Wiki的关联
4. **生成Wiki更新**: 提出Wiki页面的创建/更新建议

## 输出格式

```json
{
  "summary": "内容摘要",
  "key_points": ["要点1", "要点2"],
  "entities": [
    {"name": "实体名", "type": "类型", "description": "描述"}
  ],
  "related_pages": ["相关页面路径"],
  "wiki_updates": [
    {
      "action": "create|update",
      "page_path": "wiki/topics/xxx.md",
      "changes": "具体修改建议"
    }
  ],
  "new_tags": ["建议标签"],
  "confidence": 0.85
}
```
```

### 6.4 Query Prompt 模板

```markdown
# Query 回答 Prompt

你是一个知识库助手，基于已维护的Wiki回答用户问题。

## 用户问题
{user_query}

## 相关Wiki页面

{wiki_content}

## 回答要求

1. **基于Wiki回答**: 主要引用Wiki页面的内容
2. **标注来源**: 每个观点注明来源页面
3. **综合分析**: 不是片段拼接，而是系统性回答
4. **诚实边界**: 不确定的内容明确说明

## 回答格式

```json
{
  "answer": "综合回答...",
  "sources": [
    {"page": "页面路径", "relevance": "引用内容"}
  ],
  "confidence": 0.9,
  "suggest_new_page": true,
  "new_page_content": "如果建议创建新页，提供内容"
}
```
```

---

## 7. 存储与备份

### 7.1 存储容量估算

> **假设前提**：每日 10 条文本笔记 + 2 篇 Markdown + 1 份文档 + 3 张图片，持续增长 10 年

#### 7.1.1 基础数据增长模型

| 数据类型 | 单条大小 | 每日数量 | 年增量 | 10年总量 | 占比 |
|----------|----------|----------|--------|----------|------|
| 文本笔记 | 2-5 KB | 10 条 | 18 MB | 180 MB | 0.5% |
| Markdown 笔记 | 50-200 KB | 2 篇 | 100 MB | 1 GB | 3% |
| PDF/Word 文档 | 500 KB-5 MB | 1 份 | 500 MB | 5 GB | 14% |
| 图片附件 | 200 KB-2 MB | 3 张 | 800 MB | 8 GB | 22% |
| Wiki 页面 | 5-50 KB | 5 页增量 | 50 MB | 500 MB | 1.5% |
| **小计（原始数据）** | - | - | **~1.5 GB/年** | **~14.7 GB** | **41%** |

#### 7.1.2 向量数据增长模型

> **关键修正**：向量数据随文档量线性增长，需精确计算

| 数据类型 | 单条大小计算 | 每日数量 | 年增量 | 10年总量 | 占比 |
|----------|-------------|----------|--------|----------|------|
| Document Embedding | 1536维 × 4B = 6KB × 10 chunk/文档 | 130 chunk | 280 MB | 2.8 GB | 8% |
| Wiki Embedding | 1536维 × 4B = 6KB × 5 chunk/页 | 25 chunk | 55 MB | 550 MB | 1.5% |
| Memory Embedding | 1536维 × 4B = 6KB × 10条 | 10 条 | 22 MB | 220 MB | 0.6% |
| ChromaDB 索引开销 | 元数据 + HNSW 图结构 | - | 50 MB | 500 MB | 1.5% |
| **小计（向量数据）** | - | - | **~400 MB/年** | **~4 GB** | **11.6%** |

#### 7.1.3 数据库与索引

| 数据类型 | 说明 | 年增量 | 10年总量 | 占比 |
|----------|------|--------|----------|------|
| SQLite 数据库 | 元数据 + 关联关系 + 审计日志 | 30 MB | 300 MB | 1% |
| 全文索引 | SQLite FTS 索引 | 20 MB | 200 MB | 0.5% |
| 配置文件 | YAML + AGENTS.md + 模板 | 1 MB | 10 MB | <0.1% |
| 操作日志 | log.md + audit_logs | 10 MB | 100 MB | 0.3% |
| **小计（数据库）** | - | **~60 MB/年** | **~610 MB** | **1.9%** |

#### 7.1.4 备份与冗余

| 备份层级 | 策略 | 占用空间 | 说明 |
|----------|------|----------|------|
| 本地 Time Machine | 每小时增量，保留 24h | ~20 GB | macOS 自带 |
| 每周完整备份 | 外接 SSD，保留 4 周 | ~80 GB (4×20GB) | 滚动覆盖 |
| 云端实时同步 | Cloudflare R2，仅 wiki+db | ~500 MB | 关键数据 |
| 年度归档 | 压缩存档，永久保留 | ~10 GB/年 × N 年 | 按需增长 |

#### 7.1.5 存储总览

| 类别 | 10年总量 | 说明 |
|------|----------|------|
| 原始数据 | 14.7 GB | 文本/文档/图片/Wiki |
| 向量数据 | 4 GB | Embedding + 索引 |
| 数据库索引 | 0.6 GB | SQLite + FTS |
| **活跃数据总计** | **~19.3 GB** | 热数据（本地 SSD） |
| 备份冗余（3x） | ~58 GB | 含 Time Machine + 外接 SSD |
| **总存储需求** | **~77 GB** | 含所有备份 |

**存储分配建议**：
- 本地 SSD（256GB）：19.3 GB 活跃数据 + 20 GB Time Machine = **40 GB**
- 外接 SSD（500GB）：80 GB 每周备份 + 年度归档 = **100 GB**
- 云端 R2（100GB 免费额度）：500 MB 关键数据 = **$0/月**

> **结论**：256GB Mac Mini 可支撑 10 年使用，但建议配备 500GB 外接 SSD 用于备份。

### 7.2 存储方案

| 层级 | 存储位置 | 容量 | 用途 | 月成本 |
|------|----------|------|------|--------|
| 热数据 | macOS 本地 SSD | 20 GB | 当前年份 + 索引 | $0 |
| 温数据 | 外接 SSD | 50 GB | 历史数据 + 附件 | $0 |
| 冷数据 | Cloudflare R2 | 100 GB | 全量备份 | $1.5 |

### 7.3 备份策略

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           备份策略                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   【每日增量】 本地 Time Machine                                        │
│   ├── 触发: 自动 (每小时)                                               │
│   ├── 内容: SQLite 差异 + 新增文件                                      │
│   └── 保留: macOS 默认                                                  │
│                                                                         │
│   【每周完整】 外接 SSD                                                  │
│   ├── 触发: 每周日凌晨                                                  │
│   ├── 内容: 全量数据 (raw + wiki + db)                                  │
│   └── 保留: 最近4周                                                     │
│                                                                         │
│   【实时同步】 Cloudflare R2                                             │
│   ├── 触发: 变更时 (rclone)                                             │
│   ├── 内容: 关键数据 (wiki + db)                                        │
│   └── 保留: 永久                                                       │
│                                                                         │
│   【年度归档】 压缩存档                                                  │
│   ├── 触发: 每年1月                                                     │
│   ├── 内容: 全量压缩包                                                  │
│   └── 保留: 永久 (年度快照)                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.4 备份验证

- **每月**: 验证备份完整性 (checksum)
- **每季度**: 执行恢复演练
- **每年**: 完整数据导出验证可读性

---

### 7.5 月度 API 成本预算

> **设计原则**：混合架构（本地 Ollama + 云端 API），日常任务本地处理，复杂任务按需调用云端。

#### 7.5.1 使用量预估

基于每日使用场景：

| 操作类型 | 每日次数 | 单次 Token 消耗 | 日 Token 总量 | 月 Token 总量 |
|----------|----------|----------------|---------------|---------------|
| **Ingest 分析**（本地 Ollama） | 15 次 | 2K input + 1K output | 45K | 1.35M |
| **日常搜索**（本地 Ollama） | 10 次 | 3K input + 500 output | 35K | 1.05M |
| **复杂问答**（云端 GPT-4o-mini） | 2 次 | 5K input + 1K output | 12K | 360K |
| **Lint 巡检**（本地 Ollama） | 1 次/周 | 10K input + 2K output | 17K/周 | 68K |
| **Embedding**（OpenAI text-embedding-3-small） | 20 次 | 500 token/chunk × 10 chunk | 100K | 3M |

#### 7.5.2 成本计算

| 服务 | 定价 | 月使用量 | 月成本 | 说明 |
|------|------|----------|--------|------|
| **本地 Ollama** | $0 | 2.47M tokens | **$0** | 电费约 $1-2/月 |
| **GPT-4o-mini** | $0.15/1M input<br>$0.60/1M output | 360K input<br>72K output | $0.05<br>$0.04 | 仅复杂问答 |
| **Embedding** | $0.02/1M tokens | 3M tokens | **$0.06** | text-embedding-3-small |
| **Cloudflare R2** | $0/10GB | 500MB | **$0** | 免费额度内 |
| **月度总计** | - | - | **$0.15-2.15** | 极低 |

#### 7.5.3 不同使用强度预算

| 使用场景 | 日操作量 | 云端 API 调用 | 月成本范围 | 适合人群 |
|----------|----------|---------------|------------|----------|
| **轻度使用** | 5 条笔记 + 3 次搜索 | 仅 embedding | **$0.05-0.10** | 偶尔记录 |
| **中度使用** | 15 条笔记 + 10 次搜索 + 2 次复杂问答 | embedding + GPT-4o-mini | **$0.15-0.50** | 日常学习/工作 |
| **重度使用** | 30 条笔记 + 20 次搜索 + 5 次复杂问答 + 每周 Lint | 全量调用 | **$1-3** | 知识工作者 |
| **极端使用** | 100+ 条笔记 + 大量文档 | 批量处理 | **$5-15** | 研究/写作密集 |

#### 7.5.4 成本控制策略

```yaml
# 成本预算配置
cost_control:
  monthly_budget: $2.00  # 月度预算上限

  # 配额管理
  quotas:
    gpt4o_mini_daily_limit: 5  # 每日最多 5 次云端调用
    embedding_daily_limit: 50  # 每日最多 50 次 embedding

  # 告警规则
  alerts:
    - name: budget_50_percent
      condition: "月度费用 > $1.00"
      action: "飞书通知"

    - name: budget_80_percent
      condition: "月度费用 > $1.60"
      action: "飞书通知 + 建议切换到本地模型"

    - name: budget_exceeded
      condition: "月度费用 > $2.00"
      action: "自动切换为纯本地模式，停止云端 API 调用"

  # 降级策略
  fallback:
    when_budget_exceeded:
      complex_queries: "使用本地 Ollama 替代 GPT-4o-mini"
      embedding: "使用 nomic-embed-text 本地模型"
      notification: "通知用户预算已用完，下月恢复"
```

#### 7.5.5 成本优化建议

1. **优先本地模型**：90% 场景使用 Ollama，仅复杂推理用云端
2. **Embedding 本地化**：使用 `nomic-embed-text` 替代 OpenAI（质量差距 < 5%）
3. **缓存策略**：相同 query 缓存 24 小时，避免重复调用
4. **批量处理**：文档导入时批量 embedding，降低单次 API 开销
5. **定期审计**：每月检查 API 账单，识别异常消耗

> **结论**：个人使用场景下，月度 API 成本可控制在 $0.15-2 之间，极低。

---

## 8. 安全与隐私

### 8.1 数据安全

| 措施 | 说明 |
|------|------|
| 本地优先 | 敏感数据优先存储本地 |
| 传输加密 | HTTPS/WSS 全链路加密 |
| 访问控制 | API Token 认证 |
| 日志脱敏 | 敏感信息在日志中脱敏 |

### 8.2 隐私保护

| 措施 | 说明 |
|------|------|
| 飞书数据 | 仅接收用户主动发送的消息 |
| API密钥 | 本地配置，不上传 |
| 云端数据 | 用户确认后上传，默认本地 |

### 8.3 合规考虑

- 备份数据不含飞书认证token
- 定期清理临时文件
- 支持数据完全导出/删除

---

## 8.4 错误处理策略

> **设计原则**：个人知识库以**数据完整性优先**，任何错误都不应导致数据丢失。

### 8.4.1 错误分类与处理

| 错误类型 | 严重程度 | 示例场景 | 处理策略 | 用户通知 |
|----------|----------|----------|----------|----------|
| **数据层错误** | | | | |
| SQLite 损坏 | P0 | 数据库文件损坏/锁定 | 1. 立即停止写入<br>2. 从最近备份恢复<br>3.  WAL 回滚 | 告警 + 停止服务 |
| ChromaDB 异常 | P1 | 向量索引损坏 | 1. 重建索引（从 raw 重新 embedding）<br>2. 标记问题文档 | 告警 + 降级服务 |
| 文件系统错误 | P1 | 磁盘满/权限问题 | 1. 检查磁盘空间<br>2. 清理临时文件<br>3. 修复权限 | 告警 |
| **LLM 服务错误** | | | | |
| Ollama 超时 | P2 | 模型推理 > 30s | 1. 重试 2 次<br>2. 降级为关键词搜索<br>3. 记录失败日志 | 静默降级 |
| 云端 API 失败 | P2 | OpenAI 网络错误/配额用完 | 1. 重试 3 次（指数退避）<br>2. 切换到本地模型<br>3. 提示用户充值 | 提示切换 |
| LLM 幻觉 | P1 | 生成不存在的内容 | 1. 引用来源验证<br>2. 置信度 < 0.7 时标记<br>3. 用户反馈机制 | 标记不确定 |
| **Ingest 管线错误** | | | | |
| 文档解析失败 | P2 | PDF 格式不支持 | 1. 保存原始文件到 raw/inbox<br>2. 标记解析失败<br>3. 手动处理队列 | 提示手动处理 |
| Embedding 失败 | P2 | 文本过长/编码问题 | 1. 截断或分块重试<br>2. 跳过问题段落<br>3. 记录失败统计 | 静默处理 |
| Wiki 更新冲突 | P1 | 并发修改同一页面 | 1. 乐观锁重试<br>2. 合并冲突解决<br>3. 保留两个版本 | 提示冲突 |
| **外部服务错误** | | | | |
| 飞书 API 异常 | P2 | 消息发送失败/webhook 超时 | 1. 重试 3 次<br>2. 本地消息队列缓存<br>3. 恢复后补发 | 提示延迟 |
| 网络中断 | P1 | 完全断网 | 1. 本地缓存所有输入<br>2. 断网模式可用 CLI<br>3. 恢复后同步 | 提示离线 |

### 8.4.2 错误处理代码模式

```python
# 模式1：关键操作的事务保护
async def ingest_document(content: str):
    try:
        # 1. 保存原始数据（事务）
        raw_path = await save_to_raw(content)

        # 2. 向量化（可重试）
        embedding = await retry_with_backoff(
            create_embedding,
            max_retries=3,
            content=content
        )

        # 3. LLM 分析（可降级）
        try:
            analysis = await llm_analyze(content, timeout=30)
        except LLMTimeoutError:
            analysis = await fallback_to_local_llm(content)

        # 4. 更新 Wiki（乐观锁）
        await update_wiki_with_retry(analysis, max_retries=2)

    except CriticalError as e:
        # 回滚：删除已创建的临时文件
        await rollback_ingest(raw_path)
        raise
    finally:
        # 无论成功失败，记录审计日志
        await audit_log("ingest", status=success_or_fail)
```

```python
# 模式2：LLM 输出验证
def validate_llm_wiki_update(llm_output: dict) -> ValidationResult:
    """验证 LLM 生成的 Wiki 更新是否合理"""
    issues = []

    # 检查1：引用来源是否存在
    for ref in llm_output.get("source_refs", []):
        if not wiki_page_exists(ref):
            issues.append(f"引用页面不存在: {ref}")

    # 检查2：内容长度是否合理
    if len(llm_output.get("content", "")) > 10000:
        issues.append("内容过长，可能包含幻觉")

    # 检查3：置信度阈值
    if llm_output.get("confidence", 0) < 0.7:
        issues.append("置信度过低，需人工审核")

    return ValidationResult(
        passed=len(issues) == 0,
        issues=issues
    )
```

### 8.4.3 降级策略

```
正常模式:
  用户输入 → LLM 分析 → 向量检索 → LLM 综合回答 → 输出

降级模式1（LLM 超时）:
  用户输入 → 向量检索 → 关键词排序 → 返回 Top-3 页面 → 输出

降级模式2（向量库损坏）:
  用户输入 → SQLite FTS 全文搜索 → 返回匹配文档 → 输出

降级模式3（完全离线）:
  用户输入 → 本地缓存队列 → 显示"已保存，联网后同步"
```

### 8.4.4 错误监控与告警

| 监控指标 | 告警阈值 | 告警方式 | 响应时间 |
|----------|----------|----------|----------|
| 连续 Ingest 失败 | > 3 次/小时 | 飞书消息 + 日志 | 立即 |
| 数据库损坏 | 任何 | 飞书消息 + 停止服务 | 立即 |
| 磁盘使用率 | > 85% | 飞书消息 | 1 小时内 |
| Ollama 内存溢出 | 任何 | 自动重启 + 日志 | 自动 |
| 云端 API 费用异常 | 月预算 > 80% | 飞书消息 | 当日内 |
| 备份失败 | 连续 2 次 | 飞书消息 | 24 小时内 |

---

## 8.5 LLM 输出质量评估标准

> **核心问题**：如何确保 LLM 生成的 Wiki 内容可靠、准确、有价值？

### 8.5.1 质量评估维度

| 维度 | 评估方法 | 合格标准 | 检测频率 |
|------|----------|----------|----------|
| **准确性** | 引用来源验证 | ≥ 90% 内容可追溯到 raw 层 | 每次 Ingest |
| **完整性** | 必填字段检查 | 所有必填字段非空 | 每次生成 |
| **一致性** | 页面间交叉引用检查 | 无矛盾陈述 | Lint 巡检 |
| **可读性** | 格式/语法检查 | Markdown 渲染正常，无乱码 | 每次生成 |
| **相关性** | 人工抽检 + 用户反馈 | ≥ 80% 内容对用户有价值 | 每周抽检 |

### 8.5.2 自动化质量检测

```yaml
# 质量检查清单（每次 LLM 生成 Wiki 后自动执行）
quality_checks:
  # 基础检查
  - name: required_fields
    check: "frontmatter 包含 id, type, title, created_at, updated_at"
    action: "失败则拒绝保存"

  - name: content_length
    check: "内容长度在 100-10000 字符之间"
    action: "失败则标记待审核"

  - name: source_references
    check: "所有 source_ref 路径对应文件存在"
    action: "失败则移除无效引用"

  # 语义检查
  - name: hallucination_detection
    check: "使用 LLM 自检：'以下内容是否完全基于提供的资料？'"
    action: "置信度 < 0.7 则标记需人工审核"

  - name: contradiction_check
    check: "与已有 Wiki 页面是否存在矛盾"
    action: "发现矛盾则生成冲突报告"

  # 格式检查
  - name: markdown_valid
    check: "Markdown 语法正确，可正常渲染"
    action: "失败则自动修复格式"

  - name: link_integrity
    check: "所有 [[内部链接]] 指向的页面存在"
    action: "失败则标记死链"
```

### 8.5.3 人工抽检流程

```
每周抽检（建议周末执行）:

1. 随机抽取 10 条本周生成的 Wiki 页面
2. 对比 raw 层原始资料，评估：
   - 是否准确反映原始内容？（是/部分/否）
   - 是否有遗漏的关键信息？（是/否）
   - 是否有添加不存在的内容？（是/否）
3. 记录评分（1-5分）
4. 如果均分 < 4分：
   - 分析原因（Prompt 问题？模型问题？）
   - 调整 AGENTS.md 规则或更换模型
   - 重新生成低分页面
```

### 8.5.4 用户反馈机制

```markdown
# 在飞书/CLI 提供快速反馈指令

#feedback-good <page_id>
  → 标记该页面质量高，作为训练样本

#feedback-issue <page_id> <问题类型>
  → 问题类型：hallucination / incomplete / outdated / other
  → 记录到 quality_issues.md，用于改进 Prompt

#feedback-ignore <query_id>
  → 该次搜索/回答无价值，不计入统计
```

### 8.5.5 质量指标追踪

| 指标 | 目标值 | 测量方法 | 报告频率 |
|------|--------|----------|----------|
| Wiki 页面准确率 | ≥ 90% | 人工抽检 | 每周 |
| 幻觉发生率 | < 5% | 用户反馈 + 自检 | 每周 |
| 用户满意度 | ≥ 4/5 | 反馈评分 | 每月 |
| 自动修复率 | ≥ 80% | 格式问题自动修复比例 | 每周 |
| 冲突页面数 | < 5 页 | Lint 检测 | 每周 |

---

## 8.6 回滚与恢复操作手册

> **核心原则**：任何操作都可回滚，数据丢失恢复时间 < 30 分钟。

### 8.6.1 回滚场景与策略

| 场景 | 回滚目标 | 恢复时间 | 数据丢失风险 |
|------|----------|----------|--------------|
| Wiki 页面误删 | 最近备份 | < 5 分钟 | 上次备份后的修改 |
| 数据库损坏 | WAL 回滚 / 备份恢复 | < 10 分钟 | 极小 |
| ChromaDB 损坏 | 重建索引 | 30-60 分钟 | 无（raw 层完整） |
| LLM 生成错误内容 | 回滚到上一版本 | < 2 分钟 | 无 |
| 系统升级失败 | Docker 回滚 | < 5 分钟 | 无 |

### 8.6.2 常用恢复命令

#### 场景1：恢复误删的 Wiki 页面

```bash
# 步骤1：从备份找到最近版本
$ ls backups/weekly/
2026-W16/  2026-W15/  2026-W14/  2026-W13/

# 步骤2：恢复特定页面
$ cp backups/weekly/2026-W16/data/wiki/topics/AI与机器学习.md data/wiki/topics/

# 步骤3：验证恢复
$ pkb verify --page wiki/topics/AI与机器学习.md

# 步骤4：重建索引
$ pkb reindex --page wiki/topics/AI与机器学习.md
```

#### 场景2：SQLite 数据库损坏恢复

```bash
# 步骤1：检查 WAL 文件（自动回滚）
$ sqlite3 data/db/pkb.db "PRAGMA integrity_check;"

# 如果损坏，尝试 WAL 回滚
$ sqlite3 data/db/pkb.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 步骤2：如果 WAL 回滚失败，从备份恢复
$ mv data/db/pkb.db data/db/pkb.db.corrupted  # 备份损坏文件
$ cp backups/weekly/2026-W16/data/db/pkb.db data/db/

# 步骤3：验证恢复
$ sqlite3 data/db/pkb.db "PRAGMA integrity_check;"

# 步骤4：重建向量索引（如果需要）
$ pkb reindex --all
```

#### 场景3：ChromaDB 重建索引

```bash
# 场景：向量索引损坏或需要更换 embedding 模型

# 步骤1：备份当前索引（可选）
$ cp -r data/vectors/chroma data/vectors/chroma.backup

# 步骤2：清除损坏的索引
$ rm -rf data/vectors/chroma/*

# 步骤3：从 raw 层重新 embedding
$ pkb reindex --all --source raw/

# 步骤4：验证索引完整性
$ pkb verify --vectors
```

#### 场景4：回滚 LLM 错误生成的 Wiki 页面

```bash
# 步骤1：查看页面历史版本（如果启用版本控制）
$ pkb history --page wiki/topics/AI与机器学习.md

# 步骤2：回滚到特定版本
$ pkb revert --page wiki/topics/AI与机器学习.md --version <version_id>

# 步骤3：如果没有版本控制，从 Git 恢复
$ git checkout HEAD~1 -- data/wiki/topics/AI与机器学习.md

# 步骤4：标记问题页面
$ pkb flag --page wiki/topics/AI与机器学习.md --reason "llm_hallucination"
```

#### 场景5：完整系统恢复（灾难恢复）

```bash
# 场景：磁盘故障/系统崩溃后从零恢复

# 步骤1：安装 PKB 系统
$ git clone <repo>
$ cd pkb
$ docker-compose up -d

# 步骤2：从云端备份恢复关键数据
$ rclone sync r2:pkb-backup/latest ./restored_data/

# 步骤3：恢复数据
$ cp -r ./restored_data/raw/* ./data/raw/
$ cp -r ./restored_data/wiki/* ./data/wiki/
$ cp ./restored_data/db/pkb.db ./data/db/

# 步骤4：验证数据完整性
$ pkb verify --integrity

# 步骤5：重建向量索引
$ pkb reindex --all

# 步骤6：重启服务
$ docker-compose restart
```

### 8.6.3 恢复演练检查清单

每季度执行一次恢复演练，确保备份有效：

```markdown
## 恢复演练检查清单

### 准备阶段
- [ ] 选择要恢复的备份（最近 4 周内的一个）
- [ ] 准备测试环境（隔离的目录或测试机器）
- [ ] 记录备份的 checksum

### 恢复阶段
- [ ] 恢复 SQLite 数据库
- [ ] 验证数据库完整性（PRAGMA integrity_check）
- [ ] 恢复 raw/ 目录文件
- [ ] 恢复 wiki/ 目录文件
- [ ] 重建 ChromaDB 索引

### 验证阶段
- [ ] 随机抽查 10 条文档，验证内容完整
- [ ] 随机抽查 5 个 Wiki 页面，验证格式正确
- [ ] 执行搜索测试，验证向量检索正常
- [ ] 检查审计日志完整性

### 清理阶段
- [ ] 清理测试环境
- [ ] 记录演练结果
- [ ] 更新恢复时间估算
- [ ] 如有问题，创建修复任务
```

### 8.6.4 数据迁移路径

如果未来需要迁移到其他技术栈：

```
当前: SQLite + ChromaDB + Markdown
  ↓
导出:
  - SQLite → SQL dump / CSV
  - ChromaDB → JSON (embeddings + metadata)
  - Markdown → 保持原样（开放格式）
  ↓
目标: PostgreSQL + Milvus + Markdown
  ↓
导入:
  - SQL dump → PostgreSQL
  - JSON → Milvus
  - Markdown → 保持原样
```

```bash
# 导出命令（示例）
$ pkb export --db --format sql --output backup_2026.sql
$ pkb export --vectors --format json --output vectors_2026.json
$ pkb export --wiki --format markdown --output wiki_2026/

# 验证导出文件
$ pkb verify --export backup_2026.sql vectors_2026.json wiki_2026/
```

---

## 9. 运维规格

### 9.1 环境要求

| 环境 | 要求 |
|------|------|
| 操作系统 | macOS 14+ ( Sonoma) 或 Ubuntu 22.04+ |
| Python | 3.11+ |
| 内存 | 16 GB 推荐 (8GB 最低，Ollama需4-6GB) |
| 磁盘 | 50 GB 可用空间 |
| 网络 | 稳定互联网连接 (用于云端API) |

### 9.2 部署方式

```yaml
# docker-compose.yml 核心配置
services:
  pkb-backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///app/data/db/pkb.db
      - CHROMA_DB_PATH=/app/data/vectors/chroma
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    restart: unless-stopped

  pkb-ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  ollama_data:
```

### 9.3 监控指标

| 指标 | 告警阈值 |
|------|----------|
| 服务可用性 | < 99.5% |
| API响应时间 | > 2s |
| 磁盘使用率 | > 80% |
| 内存使用率 | > 85% |
| 备份失败 | 连续2次 |
| 向量库大小 | 异常增长 > 20%/天 |

### 9.4 日志规范

```python
# 日志格式
{
    "timestamp": "2026-04-18T10:30:00Z",
    "level": "INFO",
    "service": "pkb-ingest",
    "action": "document_processed",
    "document_id": "doc-xxx",
    "duration_ms": 1500,
    "details": {
        "source": "feishu",
        "word_count": 500,
        "entities_found": 5
    }
}
```

---

## 10. 长期可维护性

### 10.1 技术稳定性评估

| 技术 | 稳定性 | 理由 | 风险缓解 |
|------|--------|------|----------|
| Python | ★★★★★ | 30年历史，TOP3 | 语法稳定 |
| SQLite | ★★★★★ | 单文件格式20年不变 | 定期导出验证 |
| Markdown | ★★★★★ | 纯文本，永不过期 | 核心格式 |
| FastAPI | ★★★★☆ | 成熟框架 | 锁定版本 |
| ChromaDB | ★★★☆☆ | 新兴项目 | 定期导出JSON |

### 10.2 年度验证流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        年度数据验证                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. 导出全量数据                                                       │
│      $ pkb export --all --format markdown                              │
│      $ pkb export --db --output backup.sql                             │
│      $ pkb export --vectors --format json                              │
│                                                                         │
│   2. 验证完整性                                                         │
│      $ pkb verify --integrity                                          │
│      $ pkb verify --readability                                        │
│                                                                         │
│   3. 测试恢复                                                           │
│      $ pkb restore --from backup.sql --target test-env                │
│                                                                         │
│   4. 性能评估                                                           │
│      - 索引速度                                                         │
│      - 搜索延迟                                                         │
│      - 存储增长趋势                                                     │
│                                                                         │
│   5. 更新文档                                                           │
│      - 更新 AGENTS.md (如有规则调整)                                    │
│      - 更新技术栈文档                                                   │
│      - 记录年度回顾                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.3 迁移能力

所有数据格式遵循以下原则：

1. **核心数据**: Markdown/SQLite (完全开放)
2. **向量数据**: JSON 导出支持
3. **配置数据**: YAML (人类可读)
4. **文档**: PDF/A (ISO标准)

---

## 11. 附录

### 11.1 AGENTS.md 完整模板

```markdown
# PKB AGENTS.md

## 系统角色

你是一个个人知识库维护助手 (Wiki Maintainer)。
你的职责是持续维护一个结构化的个人Wiki，而非仅仅回答问题。

## 目录规则

```
root/
├── raw/           # 原始资料层，source of truth，LLM不可修改
│   ├── inbox/     # 新进入的资料
│   ├── notes/    # 日常随手记
│   ├── documents/# 上传的文档
│   └── feishu/   # 飞书归档
│
├── wiki/          # Wiki层，LLM维护
│   ├── index.md  # 知识库总览
│   ├── log.md    # 操作日志
│   ├── sources/  # 资料索引
│   ├── topics/   # 主题
│   ├── entities/ # 实体
│   ├── projects/ # 项目
│   └── decisions/ # 决策记录
│
└── CONFIG/        # 配置文件
    └── templates/ # 页面模板
```

## Ingest 规则

当新资料进入时，执行以下步骤：

1. **读取原始资料**
   - 完整理解内容
   - 提取关键信息

2. **创建/更新 Sources 页**
   - 在 `wiki/sources/` 创建对应页面
   - 包含：来源、日期、关键结论、相关页面

3. **分析关联**
   - 找出相关的 topics/entities/projects 页面
   - 如无对应页面，建议创建

4. **更新 Wiki 页面**
   - 在相关页面添加信息
   - 补全交叉链接

5. **更新索引**
   - 更新 `wiki/index.md` 的最近更新列表
   - 如有必要，更新标签

6. **记录日志**
   - 追加到 `wiki/log.md`

## Query 规则

当用户提问时，执行以下步骤：

1. **理解问题**
   - 明确查询意图
   - 确定相关主题

2. **定位 Wiki 页面**
   - 先读 `wiki/index.md`
   - 定位相关页面

3. **综合回答**
   - 基于 Wiki 页面回答
   - 引用来源链接
   - 不确定的内容明确说明

4. **评估回写价值**
   - 如果回答包含新认知
   - 建议创建/更新 Wiki 页面

## Lint 规则

每周巡检时检查：

1. **孤儿页检测**
   - 找出未被引用的页面
   - 决定：保留、合并还是归档

2. **重复检测**
   - 找出内容相似的页面
   - 合并重复内容

3. **过期标记**
   - 检测过时结论
   - 标记或更新

4. **链接检查**
   - 修复死链
   - 补全缺失链接

5. **概念提升**
   - 找出高频提及但无页面的概念
   - 建议创建新页面

## 页面规范

### 必须字段

每个 Wiki 页面必须包含：

```yaml
---
id: <uuid>
type: <topics|entities|projects|decisions>
title: <页面标题>
created_at: <ISO时间>
updated_at: <ISO时间>
tags: [<标签列表>]
related_pages:
  - <相关页面路径>
source_ref:
  - <原始资料路径>
---
```

### 页面类型特定要求

**topics/**:
- 定义
- 关键概念
- 相关项目
- 最近认知

**entities/**:
- 简介
- 类型
- 使用场景
- 相关决策

**projects/**:
- 概述
- 技术栈
- 关键决策
- 进展状态

**decisions/**:
- 背景
- 选项
- 最终决定
- 理由

## 日志规范

每次 Ingest/Lint 后追加到 `wiki/log.md`:

```markdown
## 2026-04-18

### Ingest
- 10:30 - 处理飞书消息 → 创建 [[wiki/sources/2026-04-18-xxx]]
- 10:32 - 更新 [[wiki/topics/AI与机器学习]]

### Lint
- 14:00 - 巡检完成
  - 发现1个孤儿页：xxx
  - 合并重复页面：xxx

### Query
- 15:00 - 回答"如何配置Ollama"
  - 来源：[[wiki/topics/Ollama配置]]
  - 建议创建：[[wiki/decisions/2026-04-Ollama选型]]
```

## 约束

1. **不撒谎**: 不确定的内容明确说"我不知道"
2. **引用来源**: 所有观点注明来源
3. **保持简洁**: 避免冗余内容
4. **维护一致性**: 定期检查页面间的一致性
```

### 11.2 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 个人知识库 | Personal Knowledge Base, PKB | 本系统 |
| 原始资料层 | Raw Layer | 存放原始内容，不允许LLM修改 |
| Wiki层 | Wiki Layer | LLM维护的结构化知识 |
| 规则层 | Schema Layer | 定义LLM维护行为的约束 |
| 资料摄取 | Ingest | 新资料进入系统并被处理 |
| 巡检 | Lint | 周期性质量检查 |
| 实体 | Entity | 知识图谱中的节点 |
| 记忆 | Memory | 用户记录的想法和思考 |

### 11.3 参考资料

- Karpathy, A. (2026). llm-wiki.md. GitHub Gist.
- FastAPI Documentation. https://fastapi.tiangolo.com/
- ChromaDB Documentation. https://docs.trychroma.com/
- Ollama Documentation. https://github.com/ollama/ollama
- Lark Open Platform. https://open.larksuite.com/

---

*文档版本: v1.0 | 最后更新: 2026-04-18*
