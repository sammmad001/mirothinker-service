# MiroThinker 深度研究 Agent 功能分析文档

> 版本: v1.7 | 更新日期: 2026-05-11

---

## 目录

1. [项目概述](#1-项目概述)
2. [核心架构](#2-核心架构)
3. [关键功能详解](#3-关键功能详解)
4. [MCP 工具生态系统](#4-mcp-工具生态系统)
5. [上下文管理机制](#5-上下文管理机制)
6. [Agent 配置体系](#6-agent-配置体系)
7. [基准测试评估体系](#7-基准测试评估体系)
8. [轨迹收集与训练](#8-轨迹收集与训练)
9. [模型版本对比](#9-模型版本对比)
10. [部署方案](#10-部署方案)
11. [运维与监控](#11-运维与监控)
12. [扩展与二次开发](#12-扩展与二次开发)
13. [常见问题与最佳实践](#13-常见问题与最佳实践)

---

## 1. 项目概述

### 1.1 项目定位

MiroThinker 是一个**深度研究 Agent**，专注于复杂研究任务的信息搜索、分析和推理。其核心设计理念是通过**交互式扩展 (Interactive Scaling)** —— 将工具交互深度作为继模型规模和上下文长度之后的第三个性能维度。

### 1.2 核心能力

| 能力 | 指标 |
|------|------|
| 上下文窗口 | 256K tokens |
| 最大工具调用次数 | 300 次/任务 (v1.7) |
| 支持参数规模 | 30B / 235B |
| 搜索深度 | 多步骤深度研究 |
| 基准表现 | BrowseComp 74.0%, GAIA-Val-165 82.7% |

### 1.3 适用场景

- **深度网络研究**: 需要多轮搜索、对比、验证的复杂研究任务
- **信息挖掘**: 在海量网页信息中定位特定答案
- **多步推理**: 需要代码执行、数据分析、信息综合的研究流程
- **跨语言研究**: 中英文双语研究能力

### 1.4 不适用场景

- 简单问答（单次搜索即可回答的问题）
- 实时对话交互
- 多模态直接输出（需配合外部工具）

---

## 2. 核心架构

### 2.1 系统分层架构

```
┌─────────────────────────────────────────────────────┐
│                    用户层                             │
│          CLI / Gradio Demo / API 调用                │
├─────────────────────────────────────────────────────┤
│                    Agent 层                           │
│   ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│   │ Main Agent  │→ │ Sub Agent   │→ │ Context    │  │
│   │ (主研究)    │  │ (浏览子任务) │  │ Manager    │  │
│   └──────┬──────┘  └─────────────┘  └────────────┘  │
│          │                                            │
├──────────┼────────────────────────────────────────────┤
│          │           MCP 工具层                        │
│          │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│          └─→│搜索  │ │抓取  │ │执行  │ │...   │      │
│             └──────┘ └──────┘ └──────┘ └──────┘      │
├─────────────────────────────────────────────────────┤
│                    外部服务层                          │
│   Serper API │ Jina API │ E2B Sandbox │ LLM Server   │
└─────────────────────────────────────────────────────┘
```

### 2.2 ReAct 推理循环

MiroThinker 采用 **ReAct (Reasoning + Acting)** 模式：

```
用户提问
  │
  ▼
┌─────────────┐
│  思考 (Thought) │ ← 分析当前状态，决定下一步
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  行动 (Action)  │ ← 调用 MCP 工具（搜索/代码/抓取）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  观察 (Observation)│ ← 获取工具返回结果
└──────┬──────┘
       │
       ▼
  重复思考→行动→观察...（最多 max_turns 次）
       │
       ▼
┌─────────────┐
│  最终回答 (Final Answer) │
└─────────────┘
```

### 2.3 核心组件

| 组件 | 位置 | 职责 |
|------|------|------|
| `main.py` | `apps/miroflow-agent/` | Agent 主入口，任务调度 |
| `manager.py` | `libs/miroflow-tools/src/` | MCP 工具管理器，路由工具调用 |
| MCP Servers | `libs/miroflow-tools/src/miroflow_tools/mcp_servers/` | 各工具实现 |
| Agent Configs | `apps/miroflow-agent/conf/agent/` | YAML 配置文件 |
| Benchmarks | `apps/miroflow-agent/benchmarks/` | 评估数据集和脚本 |

---

## 3. 关键功能详解

### 3.1 深度网络研究

MiroThinker 能够自主完成深度研究流程：

1. **任务分解**: 将复杂问题拆解为子问题
2. **多源搜索**: 通过 Serper API 进行多角度搜索
3. **内容抓取**: 使用 Jina 提取网页核心内容
4. **信息综合**: LLM 综合多源信息形成结论
5. **自我验证**: 交叉验证信息来源和结论
6. **报告生成**: 输出结构化研究结果

### 3.2 代码执行能力

通过 E2B 沙箱，Agent 可以：

- 执行 Python 代码进行数据分析
- 运行命令处理文本/数据
- 上传/下载文件管理中间产物
- 安全隔离执行环境

**可用工具**:

| 工具 | 功能 |
|------|------|
| `create_sandbox` | 创建执行环境 |
| `run_command` | 执行 Shell 命令 |
| `run_python_code` | 执行 Python 代码 |
| `upload_file_from_local_to_sandbox` | 上传本地文件到沙箱 |
| `download_file_from_sandbox_to_local` | 从沙箱下载文件 |
| `download_file_from_internet_to_sandbox` | 从网络下载到沙箱 |

### 3.3 网页内容提取

Jina 抓取流程：

```
URL → Jina Reader → 提取正文 → LLM 摘要 → 结构化信息
```

需要配置独立的 `SUMMARY_LLM`（推荐小模型如 Qwen3-14B 或 GPT-5-Nano，对性能影响极小）。

### 3.4 子 Agent 协作（可选）

部分配置支持多 Agent 架构：

- **Main Agent**: 负责任务规划和核心研究
- **Browsing Sub-Agent**: 专门处理网页浏览和信息提取

---

## 4. MCP 工具生态系统

### 4.1 核心工具链（最小必需）

| 工具 | API | 用途 | 获取 |
|------|-----|------|------|
| **Serper** | `google_search` | Google 搜索 | https://serper.dev/ |
| **Jina** | `scrape_and_extract_info` | 网页内容提取 | https://jina.ai/ |
| **E2B** | `run_python_code` 等 | 代码执行沙箱 | https://e2b.dev/ |

### 4.2 可选工具矩阵

| 工具 | 类型 | 能力 | 依赖 |
|------|------|------|------|
| `tool-vqa` | 商业 | Claude 视觉理解 | ANTHROPIC_API_KEY |
| `tool-vqa-os` | 开源 | 自定义视觉模型 | VISION_API_KEY |
| `tool-transcribe` | 商业 | OpenAI 语音转文字 | OPENAI_API_KEY |
| `tool-transcribe-os` | 开源 | Whisper 语音识别 | WHISPER_API_KEY |
| `tool-reasoning` | 商业 | Claude 深度推理 | ANTHROPIC_API_KEY |
| `tool-reasoning-os` | 开源 | 自定义推理模型 | REASONING_API_KEY |
| `tool-reading` | 开源 | MarkItDown 文档阅读 | 无 |
| `tool-google-search` | 商业 | Google 搜索+抓取 | SERPER_API_KEY |
| `tool-sogou-search` | 商业 | 搜狗中文搜索 | 腾讯云密钥 |

### 4.3 工具注册机制

工具通过 YAML 配置动态注册：

```yaml
main_agent:
  tools:
    - tool-python
    - search_and_scrape_webpage
    - jina_scrape_llm_summary
```

Agent 启动时自动加载对应 MCP Server，无需修改代码。

---

## 5. 上下文管理机制

### 5.1 问题背景

标准 ReAct 模式下，所有工具结果都保留在消息历史中，导致：
- 上下文利用率低（早期结果对当前决策价值低）
- 上下文空间被大量历史占据，限制了研究深度

### 5.2 解决方案：Recency-Based Context Retention

```
┌────────────────────────────────────────────────────┐
│  完整消息历史（始终保留）:                             │
│  System Prompt                                     │
│  User Question                                     │
│  All Thoughts & Actions                            │
│                                                    │
│  工具结果（仅保留最近K条）:                             │
│  [Observation N-4]  ← 保留                          │
│  [Observation N-3]  ← 保留                          │
│  [Observation N-2]  ← 保留                          │
│  [Observation N-1]  ← 保留                          │
│  [Observation N]    ← 保留                          │
│  [Observation N-5]  ← 已裁剪                        │
│  ...                                               │
└────────────────────────────────────────────────────┘
```

### 5.3 参数详解

| 值 | 行为 | 适用场景 |
|----|------|----------|
| `-1` | 保留所有工具结果 | 短任务（<50轮） |
| `5` | 保留最近5条 | **推荐**，平衡深度与聚焦 |
| `10` | 保留最近10条 | 需要更多上下文参考 |
| `1` | 仅保留最新1条 | 极度聚焦，减少干扰 |

### 5.4 效果验证

- ✅ 保留推理和行动轨迹完整性
- ✅ 聚焦最相关的上下文信息
- ✅ 释放更多空间用于深度推理
- ✅ 不会导致性能下降

---

## 6. Agent 配置体系

### 6.1 预置配置一览

| 配置文件 | 最大轮数 | 上下文策略 | 适用场景 |
|----------|----------|-----------|----------|
| `mirothinker_1.7_keep5_max200` ⭐ | 200 | 保留最近5条 | **日常研究任务** |
| `mirothinker_1.7_keep5_max300` ⭐ | 300 | 保留最近5条 | **BrowseComp/ZH** |

### 6.2 自定义配置创建

在 `apps/miroflow-agent/conf/agent/` 下创建 YAML 文件：

```yaml
# conf/agent/my_custom_config.yaml
defaults:
  - default
  - _self_

main_agent:
  tools:
    - tool-python
    - search_and_scrape_webpage
    - jina_scrape_llm_summary
  max_turns: 200

keep_tool_result: 5

# 可选: 子 Agent
sub_agents:
  agent-browsing:
    tools:
      - tool-google-search
      - tool-reading
    max_turns: 50
```

使用方式：
```bash
uv run python main.py llm=qwen-3 agent=my_custom_config llm.base_url=http://localhost:61002/v1
```

### 6.3 配置优先级

```
default.yaml → 你的配置 → CLI参数覆盖
```

CLI 参数优先级最高，如 `llm.base_url=xxx` 会覆盖 YAML 中的值。

---

## 7. 基准测试评估体系

### 7.1 支持的基准测试

| 基准 | 类型 | 描述 | 默认轮数 |
|------|------|------|:--------:|
| **GAIA-Text-103** | 通用AI助手 | 纯文本任务子集 | 8 |
| **GAIA-Val-165** | 通用AI助手 | 完整验证集 | 8 |
| **BrowseComp-EN** | 网页浏览理解 | 英文搜索任务 | 3 |
| **BrowseComp-ZH** | 网页浏览理解 | 中文搜索任务 | 3 |
| **HLE** | 终极考试 | Humanity's Last Exam | 3 |
| **HLE-Text-2158** | 终极考试 | 纯文本子集 | 3 |
| **HLE-Text-500** | 终极考试 | WebWalkerQA子集 | 3 |
| **WebWalkerQA** | 网页导航QA | 网络导航问答 | 3 |
| **Frames** | 事实推理 | 事实性/检索/推理 | 3 |
| **XBench-DeepSearch** | 深度研究 | 深度研究Agent测试 | 8 |
| **FutureX** | 未来预测 | 实时预测基准 | 8 |
| **SEAL-0** | 冲突证据QA | 冲突网页证据评估 | 8 |
| **AIME2025** | 数学竞赛 | 美国数学邀请赛 | 32 |
| **DeepSearchQA** | 深度搜索QA | Google深度搜索 | 3 |

### 7.2 评估流程

```
1. 下载测试数据
   ↓
2. 配置环境变量（LLM_MODEL, BASE_URL, AGENT_SET）
   ↓
3. 运行评估脚本 (bash scripts/run_evaluate_*.sh)
   ↓
4. 监控进度 (python benchmarks/check_progress/*.py)
   ↓
5. 使用官方评分脚本计算最终分数
```

### 7.3 评估参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `LLM_MODEL` | "MiroThinker-Agents" | 模型名称标识 |
| `BASE_URL` | "https://your-api.com/v1" | LLM 服务地址 |
| `AGENT_SET` | "mirothinker_1.7_keep5_max200" | Agent配置 |
| `MAX_CONTEXT_LENGTH` | 262144 | 上下文长度(256K) |
| `MAX_CONCURRENT` | 10 | 最大并发数 |
| `TEMPERATURE` | 1.0 | 采样温度 |
| `API_KEY` | "xxx" | API密钥 |

### 7.4 评分机制

- **LLM-as-a-Judge**: 使用 GPT 模型评估答案正确性
- **Pass@1**: 单次尝试通过率
- **Best Pass@1**: 多次运行中的最高分
- **Pass@K**: K次尝试中的最高分

---

## 8. 轨迹收集与训练

### 8.1 轨迹数据

收集的轨迹包含：
- 完整思考过程 (Thoughts)
- 工具调用序列 (Actions)
- 工具返回结果 (Observations)
- 最终答案 (Final Answer)

### 8.2 收集流程

```bash
cd apps/collect-trace

# SFT 轨迹收集（高质量教师模型）
bash scripts/collect_trace_claude37.sh   # Claude 3.7
bash scripts/collect_trace_gpt5.sh       # GPT-5

# DPO 轨迹收集（偏好数据）
bash scripts/collect_trace_qwen3.sh      # 正负样本对比
```

### 8.3 数据用途

| 数据类型 | 训练方式 | 目的 |
|----------|----------|------|
| SFT 轨迹 | 监督微调 | 学习高质量研究策略 |
| DPO 轨迹 | 偏好优化 | 优化答案质量，减少错误行为 |

---

## 9. 模型版本对比

### 9.1 MiroThinker-1.7 (最新)

| 指标 | 1.7-mini (30B) | 1.7 (235B) |
|------|:--------------:|:----------:|
| BrowseComp | - | 74.0% |
| BrowseComp-ZH | 72.3% (开源SOTA) | 75.3% |
| GAIA-Val-165 | - | 82.7% |
| HLE-Text | - | 42.9% |
| 上下文 | 256K | 256K |
| 最大工具调用 | 300 | 300 |

### 9.2 MiroThinker-v1.5 (历史)

| 指标 | v1.5-30B | v1.5-235B |
|------|:--------:|:---------:|
| BrowseComp | - | 69.8% |
| BrowseComp-ZH | 39.2% | 71.5% |
| GAIA-Val-165 | - | 80.8% |
| HLE-Text | - | 39.2% |
| 最大工具调用 | 400 | 400 |

### 9.3 MiroThinker-v1.0 (历史)

| 指标 | v1.0-8B | v1.0-30B | v1.0-72B |
|------|:-------:|:--------:|:--------:|
| BrowseComp | - | - | 47.1% |
| BrowseComp-ZH | - | - | 55.6% |
| GAIA-Text-103 | - | - | 81.9% |
| HLE-Text | - | - | 37.7% |
| 最大工具调用 | 600 | 600 | 600 |

### 9.4 版本演进趋势

```
v1.0 → v1.5 → 1.7
  │       │      │
  │       │      └─ 交互式扩展: 300次工具调用，256K上下文
  │       └─ 统一DPO训练，扩展上下文到64K→256K
  └─ 引入交互式扩展概念，多尺度模型(8B/30B/72B)
```

---

## 10. 部署方案

### 10.1 SGLang 部署（推荐）

```bash
NUM_GPUS=4
PORT=61002
AGENT_PATH=miromind-ai/MiroThinker-1.7-mini

python3 -m sglang.launch_server \
    --model-path $AGENT_PATH \
    --tp $NUM_GPUS \
    --dp 1 \
    --host 0.0.0.0 \
    --port $PORT \
    --trust-remote-code
```

| 参数 | 说明 | 建议值 |
|------|------|--------|
| `--tp` | 张量并行GPU数 | 30B用2-4, 235B用8+ |
| `--dp` | 数据并行副本数 | 按需增加吞吐量 |
| `--port` | 服务端口 | 61002 |

### 10.2 vLLM 部署

与 SGLang 类似，使用 `vllm.entrypoints.openai.api_server` 启动。

### 10.3 量化部署

项目提供完整的量化部署指导（见 `apps/gradio-demo/`）：

| 方案 | 工具 | 适用场景 |
|------|------|----------|
| llama.cpp | GGUF量化 | CPU推理，Mac部署 |
| Ollama | 量化格式 | 本地快速原型 |
| SGLang | INT4/INT8 | GPU高效推理 |
| vLLM | AWQ/GPTQ | GPU高效推理 |

### 10.4 云端 API 接入

任何兼容 OpenAI API 格式的 LLM 服务都可接入：

```bash
# Claude
uv run python main.py llm=claude-3-7 agent=single_agent_keep5

# GPT-5
uv run python main.py llm=gpt-5 agent=single_agent_keep5

# 自定义 OpenAI 兼容服务
uv run python main.py llm=qwen-3 agent=mirothinker_1.7_keep5_max200 \
    llm.base_url=http://your-server:port/v1
```

---

## 11. 运维与监控

### 11.1 进度监控

```bash
python benchmarks/check_progress/check_progress_<benchmark>.py /path/to/logs
```

输出信息：
- 已完成任务数 / 总任务数
- 已耗时
- 预计剩余时间

### 11.2 日志管理

Agent 运行日志保存在 `apps/miroflow-agent/logs/` 目录，包含：
- 每轮思考过程
- 工具调用详情
- 错误堆栈

### 11.3 可视化 Trace

```bash
cd apps/visualize-trace
uv sync
python run.py
```

提供 Web UI 查看 Agent 执行轨迹：
- 时间线可视化
- 工具调用耗时
- 推理链展示

### 11.4 性能调优

| 问题 | 解决方案 |
|------|----------|
| OOM | 减小 `MAX_CONTEXT_LENGTH` 或使用 `keep_tool_result: 5` |
| 并发过高 | 减小 `MAX_CONCURRENT` 到 5 |
| 速度慢 | 增加 GPU 或量化部署 |
| 工具调用失败 | 检查对应 API Key 和网络 |

---

## 12. 扩展与二次开发

### 12.1 添加新 MCP 工具

1. 在 `libs/miroflow-tools/src/miroflow_tools/mcp_servers/` 创建新 Server
2. 继承 MCP 协议实现工具接口
3. 在 YAML 配置中注册工具名称

### 12.2 修改 Agent 行为

- **思考 Prompt**: 修改 chat template jinja
- **工具选择**: 修改 YAML 配置的 tools 列表
- **最大轮数**: 修改 max_turns 参数
- **上下文策略**: 修改 keep_tool_result 参数

### 12.3 自定义评估

```python
# 在 benchmarks/ 下创建评估器
from benchmarks.evaluators import BaseEvaluator

class MyEvaluator(BaseEvaluator):
    def evaluate(self, prediction, reference):
        # 自定义评估逻辑
        pass
```

### 12.4 与 LobeHub 集成

项目提供 LobeHub 兼容性适配器：

```
apps/lobehub-compatibility/
├── MiroThinkerToolParser.py   # 工具解析器
├── chat_template.jinja        # 聊天模板
└── test_tool_parser.py        # 测试
```

---

## 13. 常见问题与最佳实践

### 13.1 FAQ

**Q: 哪个版本适合我？**

| 需求 | 推荐 |
|------|------|
| 生产使用 | MiroThinker-1.7-mini (30B) |
| 追求极致性能 | MiroThinker-1.7 (235B) |
| 资源有限 | Claude 3.7 / GPT-5 直接调用 |

**Q: 最小配置需要哪些 API Key？**

- `SERPER_API_KEY` — Google 搜索
- `JINA_API_KEY` — 网页抓取
- `E2B_API_KEY` — 代码执行
- `SUMMARY_LLM_*` — 内容摘要（可复用已有LLM）

**Q: 如何快速测试？**

编辑 `main.py` 第32行的 `task_description`，运行：
```bash
uv run python main.py llm=qwen-3 agent=mirothinker_1.7_keep5_max200 llm.base_url=xxx
```

### 13.2 最佳实践

1. **从小配置开始**: 先用 `max200` 配置测试，确认工作正常后再增加深度
2. **监控资源**: 长时间评估时定期检查进度和日志
3. **合理选择模型**: 30B 模型性价比高，235B 模型用于追求极致准确率
4. **定期备份日志**: 评估结果和轨迹数据很有价值
5. **使用上下文管理**: `keep_tool_result: 5` 在几乎所有场景下都优于全保留

### 13.3 陷阱与注意事项

| 陷阱 | 说明 |
|------|------|
| URL 格式 | 必须以 `/v1` 结尾，如 `http://localhost:61002/v1` |
| 信息泄露 | 评估时需屏蔽benchmark答案来源网站 |
| Canary 字符串 | 评估时检测工具输出是否泄露benchmark答案 |
| 工具限流 | Serper 等 API 有速率限制，注意控制并发 |

---

## 附录

### A. 项目结构总览

```
MiroThinker/
├── apps/
│   ├── miroflow-agent/           # 核心 Agent 应用
│   │   ├── main.py               # 入口
│   │   ├── conf/agent/           # Agent 配置
│   │   ├── benchmarks/           # 评估基准
│   │   └── scripts/              # 运行脚本
│   ├── collect-trace/            # 轨迹收集
│   ├── visualize-trace/          # 轨迹可视化
│   └── lobehub-compatibility/    # LobeHub 兼容
├── libs/
│   └── miroflow-tools/           # MCP 工具库
│       └── src/miroflow_tools/
│           ├── mcp_servers/      # 各工具实现
│           └── manager.py        # 工具管理器
├── assets/                       # 图片与资源
├── README.md                     # 项目文档
└── justfile                      # 任务运行器
```

### B. 相关论文

- **MiroThinker-1.7**: [arXiv:2603.15726](https://arxiv.org/pdf/2603.15726)
- **MiroThinker-v1.0**: [arXiv:2511.11793](https://arxiv.org/abs/2511.11793)
- **MiroFlow Framework**: [arXiv:2602.22808](https://arxiv.org/abs/2602.22808)

### C. 资源链接

| 资源 | 链接 |
|------|------|
| 在线体验 | https://dr.miromind.ai/ |
| HuggingFace 模型 | https://huggingface.co/collections/miromind-ai/mirothinker-17 |
| MiroVerse 数据集 | https://huggingface.co/datasets/miromind-ai/MiroVerse-v0.1 |
| 官网 | https://miromind.ai/ |
| Discord | https://discord.com/invite/GPqEnkzQZd |
| GitHub | https://github.com/MiroMindAI/MiroThinker |

---

*本文档基于 MiroThinker v1.7 编写，其他版本的差异请参考各版本对应说明。*
