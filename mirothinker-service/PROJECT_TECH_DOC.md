# MiroThinker 深度研究 AI Agent — 完整技术文档

> 版本: 2.0.0 (五阶段深度推理架构)  
> 日期: 2026-05-15  
> 官网: [mmaoresearch.com](https://mmaoresearch.com)  
> 作者: Qoder

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [五阶段深度推理架构](#3-五阶段深度推理架构)
4. [模块功能详解](#4-模块功能详解)
5. [核心实现机制](#5-核心实现机制)
6. [部署与运维](#6-部署与运维)
7. [成本分析](#7-成本分析)

---

## 1. 项目概述

### 1.1 目标与定位

MiroThinker 是一个面向复杂研究场景的自主 AI Agent 系统。核心设计哲学:

- **深度 > 广度**: 聚焦单一问题的纵深分析，而非浅层信息罗列
- **自主 > 引导**: Agent 自主决定搜索策略、信息来源、分析角度，人类仅需提供研究问题
- **质量 > 速度**: 通过多层质量检查(Quality Pipeline)和深度质量评估(DepthQuality)确保输出可靠性
- **推理 > 搜索**: 从"搜索驱动"演进为"分析方法论驱动"，搜索是服务于推理的工具

### 1.2 核心需求

| 需求维度 | 具体要求 |
|---------|---------|
| **自主性** | Agent 能自主决定搜索策略、信息来源、分析角度，无需人工干预每一步 |
| **多轮搜索** | 支持 8~200+ 轮搜索迭代，根据信息饱和度动态调整深度 |
| **领域适配** | 7 大领域(金融/科技/健康/产业/政策/宏观/通用)，差异化研究框架 |
| **动态方法论** | 分析方法论由 LLM 根据问题内容动态生成，非固定模板 |
| **可追溯性** | 每个关键声明必须有来源引用，报告附带来源列表和可信度评分 |
| **因果链** | 每个发现必须追问 WHY 至少两层，构建完整因果链(A→B→C→结论) |
| **持久化** | 任务状态 + 研究会话快照 + 方法论模式，全部持久化存储 |
| **方法论收敛** | 历史研究会话可检索复用，高频方法论自动提取统计 |
| **并发控制** | 限制最大并发任务数，避免资源耗尽和 API 限流 |

### 1.3 技术栈

| 层级 | 技术选型 |
|-----|---------|
| **后端框架** | FastAPI + Uvicorn + asyncio |
| **LLM 引擎** | 阿里云百炼 (DashScope) |
| **搜索工具** | DuckDuckGo (ddgs) + Trafilatura (零成本) |
| **可选搜索** | Serper API / Jina API |
| **持久化** | SQLite (任务存储 + 会话存储 + 方法论模式) |
| **异步框架** | asyncio + httpx |
| **部署** | systemd + Nginx + Linux 服务器 |
| **前端** | 原生 HTML/CSS/JS (静态页面) |
| **域名** | mmaoresearch.com |

---

## 2. 系统架构

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      接入层 (API Layer)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ /api/research│  │ /api/status  │  │ /api/health      │  │
│  │ POST/GET     │  │ GET          │  │ Feishu Webhook   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      编排层 (Orchestration)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ResearchAgent.run() — 主入口             │  │
│  │  Navigator → Pre-search → Three-Phase Loop          │  │
│  │  → Quality Check → Depth Quality → Session Store    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  │
│  │ Task Store  │  │  Semaphore  │  │  Session Store     │  │
│  │  (SQLite)   │  │  (asyncio)  │  │  (SQLite)          │  │
│  └─────────────┘  └─────────────┘  └────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      能力层 (Capability Layer)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Search  │  │  Domain  │  │ Quality  │  │  Critic  │  │
│  │  (ddgs)  │  │ Registry │  │ Pipeline │  │  Review  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Research │  │Reflection│  │  Depth   │  │ Session  │  │
│  │  Memory  │  │  Node    │  │ Quality  │  │  Store   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │  Agent   │  │  Source  │  │Contradict│                │
│  │  State   │  │Credibility│  │ Detector │                │
│  └──────────┘  └──────────┘  └──────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 完整请求生命周期

```
1. 用户提交研究问题 (POST /api/research)
        |
2. Navigator 路由 (navigate): 单次 qwen-flash 调用
   输出: RoutingResult {tier, domain, subtype, budget, model_config}
        |
3. 创建任务记录 (task_store.create_task) → SQLite
   状态: pending → running
        |
4. 并发控制 (asyncio.Semaphore, MAX=2)
        |
5. 预搜索阶段 (Pre-search)
   - search_with_recency: 时效性感知搜索
   - 领域核心来源: DomainConfig.pre_search_strategy
   - 强制角度查询: mandatory_angle_queries
        |
6. 路由决策:
   IF ENABLE_THREE_PHASE_LOOP=True:
     → 进入三阶段循环 (Phase 3)
   ELSE:
     → 进入传统线性循环
        |
7. 三阶段循环 (Three-Phase Loop)
   Phase 1 PLANNING:
     - LLM 分析 query → 生成研究主线(MainThreads)
     - 为每条主线动态生成专属分析方法论
     - 提取历史相似会话的方法论作为参考
   Phase 2 DEEP_ANALYSIS:
     - 按主线深入分析，每轮注入当前主线的动态方法论
     - ResearchMemory 实时沉淀发现、因果链、假设、证据
     - ReflectionNode 每5轮自动反思并生成改进指令
     - DepthQualityPipeline 在3个质量检查点评估深度
   Phase 3 SYNTHESIS:
     - 基于完整 ResearchMemory 生成综合报告
     - 自动引用因果链和证据支撑
     - 运行质量检查 + 深度质量评估
        |
8. 条件审查 (Conditional Critic)
   TIER_1: 跳过 | TIER_2: score<0.50触发 | TIER_3: score<0.70触发
        |
9. 会话持久化 (SessionStore)
   - 保存完整会话快照到 analysis_sessions 表
   - 提取/更新方法论模式到 methodology_patterns 表
        |
10. 更新任务状态 → SQLite
        |
11. 用户轮询获取结果 (GET /api/research/{task_id})
```

---

## 3. 五阶段深度推理架构

### 3.1 Phase 0: 系统提示重构 — 从搜索驱动到分析方法论驱动

**核心变更**: 系统提示从"搜索指令集合"重构为"分析方法论框架"。

旧范式:
```
你是研究助手。使用 google_search 和 scrape_webpage 工具搜索信息...
(搜索指令占系统提示 80%)
```

新范式:
```
你是MiroThinker深度研究Agent。你的核心能力是分析推理，不是搜索罗列。

## 分析方法论(MUST FOLLOW)
1. 深度优先: 每个发现必须追问WHY至少两层，构建完整因果链
2. 逻辑链完整: 每个结论需展示完整推导过程，不可跳步
3. 假设驱动: 先形成假设→搜索验证证据→接受/修正/否定假设
4. 多维交叉: ≥2对立视角、≥5来源。关键声明须≥2独立来源验证
5. 深度分层: L1=表象→L2=直接原因→L3=根因→L4=系统理解
6. 不确定性标注: 区分"已确认"/"推测"/"有争议"

## 工具使用
搜索是服务于分析的工具，不是目的。搜索→分析→验证→深入，循环推进。
```

**效果**: 系统提示从 2000+ tokens 的搜索指令压缩为 ~800 tokens 的分析方法论，为后续思考链和动态方法论留出 token 预算。

### 3.2 Phase 1: ResearchMemory — 结构化知识沉淀

**问题**: 传统 Agent 仅依赖对话上下文，随着轮次增加，早期重要发现被上下文窗口丢弃，导致研究碎片化、无法构建完整因果链。

**解决方案**: 独立于对话上下文的结构化知识库。

#### 核心数据结构

```python
@dataclass
class Finding:
    content: str           # 发现内容
    confidence: float      # 置信度 0-1
    source_urls: list      # 来源URL
    depth_level: int       # L1/L2/L3/L4
    turn: int              # 发现轮次
    thread_title: str      # 所属主线

@dataclass
class CausalChain:
    chain_id: str
    events: list           # [{event, cause_of_next}]
    confidence: float
    supporting_sources: list

@dataclass
class Hypothesis:
    statement: str
    status: str            # pending/verified/rejected
    evidence_for: list
    evidence_against: list
    confidence: float

@dataclass
class Evidence:
    content: str
    supports: str          # 支持的假设ID
    source_url: str
    reliability: float

@dataclass
class OpenQuestion:
    question: str
    priority: int
    related_thread: str
    status: str            # open/answered

@dataclass
class MainThread:
    title: str
    questions: list
    status: str            # active/complete/paused
    findings_count: int
```

#### MemoryExtractor

每完成一轮搜索，使用 qwen-flash 从 Assistant 输出中提取结构化知识:

```python
class MemoryExtractor:
    async def extract(self, turn_content: str, turn_number: int) -> dict:
        """提取 Finding / CausalChain / Hypothesis / Evidence / OpenQuestion"""
        # 使用 qwen-flash ( cheapest model )
        # 输出结构化 JSON
```

**Token 成本**: 每次提取约 500-1000 tokens，使用 qwen-flash (~0.5 元/百万 tokens)，单次研究(35轮)提取成本约 0.02 元。

#### ResearchMemory 方法

```python
class ResearchMemory:
    def add_finding(self, finding: Finding)
    def add_causal_chain(self, chain: CausalChain)
    def add_hypothesis(self, hypothesis: Hypothesis)
    def add_evidence(self, evidence: Evidence)
    def get_context_for_next_turn(self, max_tokens=2000) -> str
    def get_causal_chains_summary(self) -> str
    def get_hypotheses_summary(self) -> str
    def to_synthesis_context(self) -> str
    def estimate_token_count(self) -> int
```

### 3.3 Phase 2: ReflectionNode — 自动反思节点

**问题**: Agent 在长时间研究中可能偏离主线、重复搜索、或停留在浅层分析。

**解决方案**: 每完成 5 轮搜索，自动触发反思评估。

#### 反思报告结构

```python
@dataclass
class ReflectionReport:
    depth_assessment: dict      # 各主线深度评估
    coverage_gaps: list         # 覆盖缺口
    logical_inconsistencies: list  # 逻辑不一致
    next_actions: list          # 下阶段改进指令
    should_terminate: bool      # 是否建议终止
```

#### 反思提示模板

```
你是一名研究质量审查员。基于以下研究记忆，评估当前研究质量:

## 研究记忆摘要
{memory_summary}

## 评估维度
1. 深度: 每条主线达到了哪个层级?(L1表象/L2直接原因/L3根因/L4系统理解)
2. 覆盖: 是否有重要角度尚未探索?
3. 一致性: 发现之间是否存在矛盾?
4. 冗余: 是否有重复搜索?

## 输出
- 深度评估: ...
- 覆盖缺口: ...
- 改进指令: ...
- 建议终止: true/false
```

**效果**: 将"盲目搜索"转化为"目标驱动的深度探索"。

### 3.4 Phase 3: Three-Phase Loop — 三阶段循环

**问题**: 传统线性搜索循环缺乏结构性，Agent 容易在同一层面打转，难以组织深度分析。

**解决方案**: 将研究过程重构为三个有明确定义的阶段。

#### Phase 1: Planning — 规划阶段

**目标**: LLM 自主规划研究结构，而非人类预设模板。

```python
class PlanningPhase:
    PLANNING_PROMPT = """
    你是一名研究规划专家。分析以下问题，生成研究计划:

    问题: {query}
    领域: {domain}
    预搜索结果: {pre_search_results}

    ## 输出要求(JSON)
    {
      "main_threads": [
        {
          "title": "主线标题",
          "questions": ["子问题1", "子问题2"],
          "analysis_methodology": "该主线的专属分析方法论..."
        }
      ],
      "hypotheses": ["假设1", "假设2"],
      "search_strategy": "搜索策略"
    }
    """
```

**关键设计**: `analysis_methodology` 必须根据该主线的具体内容特点来定义，不可泛泛而谈。

例如:
- 主线"特斯拉 Q3 毛利率下滑原因" → 方法论聚焦: 成本归因链(原材料/人工/制造费用)、产能利用率影响、与同行对比
- 主线"美联储政策对特斯拉融资成本影响" → 方法论聚焦: 利率传导机制、债务结构敏感性、期权定价隐含波动

#### Phase 2: DeepAnalysis — 深度分析阶段

```python
class DeepAnalysisPhase:
    async def execute(self, plan: ResearchPlan, memory: ResearchMemory, ...):
        for thread in plan.main_threads:
            # 为当前主线构建专属系统提示
            thread_methodology = plan.thread_methodologies.get(thread.title, "")
            # 注入动态方法论到系统提示
            thread_directive = f"当前研究主线: {thread.title}\n{thread_methodology}"
            # 执行该主线的深入搜索和分析
            ...
```

**设计要点**:
- 每轮聚焦单一主线，避免上下文混乱
- 注入该主线的专属方法论，确保分析深度
- ResearchMemory 实时沉淀发现
- ReflectionNode 每5轮评估并生成改进指令

#### Phase 3: Synthesis — 综合阶段

```python
class SynthesisPhase:
    async def execute(self, query, plan, memory, domain, ...):
        # 使用完整的 ResearchMemory 作为输入
        synthesis_context = memory.to_synthesis_context()
        # LLM 基于结构化知识生成综合报告
        # 自动引用因果链、假设验证状态、证据支撑
```

**优势**:
- 综合阶段不依赖对话上下文，直接使用结构化知识
- 因果链自动嵌入报告
- 假设验证状态清晰展示
- 证据与结论的对应关系可追溯

### 3.5 Phase 4: Dynamic Methodology — 动态方法论

**问题**: 最初设计为每个领域固定一套分析方法论(如金融领域固定"财务归因链/竞争动态/估值逻辑")，导致不同问题使用相同模板，过于僵化。

**解决方案**: 方法论由 LLM 根据问题内容动态生成，存储在 Planning 的输出中。

#### 实现机制

1. **PlanningPhase 生成**: 每条主线的 `analysis_methodology` 由 Planning LLM 根据问题内容、预搜索结果、领域特征动态生成。

2. **DeepAnalysisPhase 注入**: 执行到某主线时，将该主线的专属方法论注入系统提示:
```python
thread_methodology = plan.thread_methodologies.get(thread_title, "")
if thread_methodology:
    thread_directive += f"\n## 本主线分析方法论(根据问题内容动态定义)\n{thread_methodology}\n"
```

3. **历史方法论复用**: PlanningPhase 检索历史相似会话，提取其方法论作为参考:
```python
similar_sessions = session_store.find_similar_sessions(query, limit=3)
historical_methodologies = [s.thread_methodologies for s in similar_sessions]
```

#### 对比

| 维度 | 固定领域方法论 | 动态方法论 |
|------|-------------|-----------|
| 生成时机 | 开发时硬编码 | 运行时根据问题生成 |
| 适配性 | 同一领域所有问题共用 | 每条主线专属定制 |
| 示例 | 所有金融问题→"财务归因链/竞争动态/估值逻辑" | "特斯拉毛利率"→成本归因链；"美联储降息"→利率传导机制 |
| 演进 | 需手动修改代码 | 随历史会话自动收敛丰富 |

### 3.6 Phase 5: DepthQualityPipeline — 深度质量评估

**问题**: 传统质量检查(QualityCheckPipeline)评估的是"报告写得好不好"(结构、语言、引用)，但无法评估"研究够不够深"。

**解决方案**: 五维深度评估，专门衡量研究的认知深度。

#### 五维评估指标

```python
class DepthQualityPipeline:
    def evaluate(self, report: str, memory: ResearchMemory, metadata: dict) -> DepthQualityReport:
        return {
            "depth_distribution": {...},      # L1/L2/L3/L4 覆盖率
            "causal_chains": {...},           # 因果链数量、平均长度、闭环比例
            "logic_chains": {...},            # 推导步骤数、跳步比例、置信度标注
            "hypothesis_verification": {...}, # 假设数量、验证率、反证考虑
            "evidence_support": {...},        # 关键声明证据覆盖率、来源独立性
            "overall_depth_score": float,     # 综合深度得分 0-1
            "recommendations": list,          # 改进建议
        }
```

#### 深度层级定义

| 层级 | 名称 | 特征 |
|-----|------|------|
| L1 | 表象 | 发生了什么(事实陈述) |
| L2 | 直接原因 | 为什么会发生(第一层因果) |
| L3 | 根因 | 根本原因是什么(系统性因素) |
| L4 | 系统理解 | 如何改变/预测(机制性理解) |

#### 质量检查点

深度质量评估在三个关键节点执行:
1. **Planning 后**: 评估规划本身的深度预期
2. **DeepAnalysis 中**: 每完成一轮主线分析，评估当前深度
3. **Synthesis 后**: 评估最终报告的输出深度

#### 得分计算

```python
def _calculate_depth_score(self, evaluation: dict) -> float:
    weights = {
        "depth_distribution": 0.25,
        "causal_chains": 0.25,
        "logic_chains": 0.20,
        "hypothesis_verification": 0.15,
        "evidence_support": 0.15,
    }
    score = sum(evaluation[k]["score"] * w for k, w in weights.items())
    return round(min(score, 1.0), 2)
```

---

## 4. 模块功能详解

### 4.1 Navigator 智能路由 (`src/navigator/`)

**能力**: 单次 LLM 调用完成查询分类、预算分配、模型选择。

| 组件 | 文件 | 功能 |
|-----|------|------|
| `navigate()` | `router.py` | 主入口: 分类→预算→模型选择→RoutingResult |
| `_classify_with_llm()` | `router.py` | qwen-flash调用, JSON解析 |
| `build_classify_prompt()` | `classify_prompt_builder.py` | 动态从 DOMAIN_REGISTRY 生成分类提示 |
| `allocate_budget()` | `budget_allocator.py` | 按 tier 分配 max_turns/context_keep |
| `select_models()` | `budget_allocator.py` | 按 tier 选择 search/synthesis/critic 模型 |

**TIER 配置**:

| Tier | max_turns | context_keep | search_model | synthesis_model | critic |
|------|-----------|--------------|--------------|-----------------|--------|
| TIER_1 | 8 | 2 | qwen-turbo | qwen-plus | 无 |
| TIER_2 | 20 | 3 | qwen-turbo | qwen3.6-plus | qwen-flash |
| TIER_3 | 35 | 4 | qwen-turbo | qwen3.6-plus | qwen-flash |

### 4.2 Agent 核心引擎 (`src/services/agent.py`)

| 类/函数 | 功能 |
|---------|------|
| `ResearchAgent` | 核心 Agent 类，整合所有能力模块 |
| `ResearchAgent.run()` | 主执行入口: 路由→预搜索→三阶段循环/传统循环→质量→审查→持久化 |
| `ResearchAgent._run_three_phase()` | 三阶段循环执行 (Phase 3) |
| `ResearchAgent._run_legacy()` | 传统线性搜索循环 (向后兼容) |
| `ResearchAgent.call_llm()` | DashScope API 封装，180s 超时 |
| `build_system_prompt()` | 构建分析方法论驱动的系统提示 (Phase 0/4) |
| `AgentState` | 对话状态管理 + ResearchMemory 集成 |
| `AgentState.get_context_window()` | 动态上下文窗口(去重+摘要+source汇总+Memory注入) |
| `AgentState.is_duplicate_search()` | Jaccard 相似度>0.85 判定重复 |

### 4.3 搜索与抓取 (`src/services/search.py`)

| 类/函数 | 功能 |
|---------|------|
| `ToolClient` | 工具客户端，整合搜索+抓取+缓存 |
| `ToolClient.google_search()` | DuckDuckGo 搜索，max_results=3 |
| `ToolClient.search_with_recency()` | 时效性搜索(近1月→财报专用→近1年→通用) |
| `ToolClient.scrape_webpage()` | Trafilatura 抓取，返回 400 字符 |
| `SearchCache` | 内存缓存，1 小时 TTL |
| `DateExtractor` | 从搜索结果提取日期(5种策略) |

### 4.4 质量系统 (`src/services/quality.py`)

| 类/函数 | 功能 |
|---------|------|
| `QualityCheckPipeline` | 7维通用检查 + 领域特定检查 |
| `FixedChannelSearch` | 固定渠道搜索(指定站点深度检索) |
| `SourceCredibilityScorer` | 信源可信度评分 |
| `ContradictionDetector` | 矛盾检测器 |
| `QualityCheckPipeline.run()` | 执行质量检查 → overall_score |

### 4.5 ResearchMemory (`src/services/research_memory.py`)

| 类/函数 | 功能 |
|---------|------|
| `ResearchMemory` | 结构化知识库 |
| `ResearchMemory.init_from_plan()` | 从 ResearchPlan 初始化主线和假设 |
| `ResearchMemory.set_session_metadata()` | 存储 query + domain + thread_methodologies |
| `ResearchMemory.log_reasoning()` | 记录推理过程日志 |
| `ResearchMemory.to_session_snapshot()` | 导出完整会话快照 |
| `ResearchMemory.to_synthesis_context()` | 生成综合阶段输入上下文 |
| `MemoryExtractor` | 使用 qwen-flash 从对话中提取结构化知识 |

### 4.6 SessionStore (`src/core/session_store.py`)

| 函数 | 功能 |
|------|------|
| `save_session()` | 保存会话快照到 analysis_sessions 表 |
| `get_session()` | 按 ID 检索会话 |
| `list_sessions()` | 分页列出历史会话 |
| `find_similar_sessions()` | 基于 query 相似度检索 |
| `get_methodology_patterns()` | 获取高频方法论模式 |
| `get_session_stats()` | 会话统计信息 |

**数据库表结构**:

```sql
CREATE TABLE analysis_sessions (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    domain TEXT,
    tier TEXT,
    status TEXT,
    thread_methodologies TEXT,  -- JSON
    reasoning_log TEXT,         -- JSON
    memory_snapshot TEXT,       -- JSON
    report_text TEXT,
    depth_quality_score REAL,
    overall_quality_score REAL,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE methodology_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT,
    pattern_text TEXT,
    usage_count INTEGER DEFAULT 1,
    avg_depth_score REAL,
    first_seen TIMESTAMP,
    last_used TIMESTAMP
);
```

### 4.7 三阶段模块 (`src/services/phases/`)

| 文件 | 类 | 功能 |
|------|-----|------|
| `planning.py` | `PlanningPhase` | 生成 ResearchPlan(主线+假设+方法论) |
| `planning.py` | `ResearchPlan` | 研究计划数据类，含 thread_methodologies |
| `deep_analysis.py` | `DeepAnalysisPhase` | 按主线执行深度分析，注入动态方法论 |
| `synthesis.py` | `SynthesisPhase` | 基于 ResearchMemory 生成综合报告 |
| `synthesis.py` | `SynthesisResult` | 综合结果(报告+统计) |

### 4.8 深度质量 (`src/services/depth_quality.py`)

| 类/函数 | 功能 |
|---------|------|
| `DepthQualityPipeline` | 五维深度评估 |
| `DepthQualityPipeline.evaluate()` | 评估报告深度 |
| `integrate_depth_quality()` | 在 Agent 中集成深度质量检查点 |

### 4.9 领域系统 (`src/domains/`)

**7 大领域**:

| 领域 | 文件 | 子类型数 | 思考链数 |
|------|------|---------|---------|
| 金融 | `finance.py` | 12 | 6 |
| 科技 | `tech.py` | 8 | 5 |
| 健康 | `health.py` | 6 | 5 |
| 产业 | `industry.py` | 8 | 4 |
| 政策 | `policy.py` | 6 | 4 |
| 宏观 | `macro.py` | 6 | 4 |
| 通用 | `general.py` | 4 | 3 |

**DomainConfig 结构**:
```python
@dataclass
class DomainConfig:
    name: str
    description: str
    keywords: list
    thinking_chains: list
    quality_rules: list
    pre_search_strategy: dict
    mandatory_angle_queries: list
    analysis_methodology: str  # 保留但不再固定注入提示
```

---

## 5. 核心实现机制

### 5.1 Token 预算管理

**总预算**: 50万 tokens/请求 (qwen3.6-plus 上限)

| 组件 | Token 预算 | 占比 |
|------|-----------|------|
| 系统提示 | ~1,500 | 3% |
| 动态方法论(每主线) | ~500 | 1% |
| 对话上下文 | ~8,000 | 16% |
| ResearchMemory 注入 | ~2,000 | 4% |
| 搜索结果 | ~15,000 | 30% |
| LLM 输出 | ~20,000 | 40% |
| 安全余量 | ~3,000 | 6% |
| **总计** | **~50,000** | **~100%** |

**优化措施**:
- 搜索结果单行压缩: `标题|链接|摘要(80字符)`
- 工具结果去重: URL 级别去重，相同来源只保留一次
- 上下文自动摘要: 超过 1500 字符的 assistant 消息自动压缩
- Source 汇总: 多轮搜索结果合并为统一 source 列表

### 5.2 反循环机制

```python
# 1. 精确去重
normalized = query.strip().lower()
if normalized in self.searched_queries:
    return True  # 完全重复

# 2. 模糊去重 (Jaccard 相似度)
for recent in self.search_history[-5:]:
    if self._query_similarity(normalized, recent) > 0.85:
        return True  # 高度相似

# 3. 最小研究保护
if turn_count < 3 and sources_count < 3:
    # 拒绝 premature FINAL ANSWER，强制继续搜索
```

### 5.3 智能早停

```python
# 触发条件(满足任一):
1. 连续 3 轮无工具调用 (信息已充足)
2. 累计来源 ≥ 25 个 (来源饱和)
3. 达到 max_turns (预算耗尽)
4. ReflectionNode 建议终止
5. 所有主线完成 (三阶段循环)
```

### 5.4 分层模型策略

| 阶段 | 模型 | 原因 |
|------|------|------|
| Navigator 分类 | qwen-flash | 简单分类任务，最省成本 |
| 搜索循环 | qwen-turbo | 工具调用为主，不需要最强推理 |
| 综合分析 | qwen3.6-plus | 需要深度推理和结构化输出 |
| 审查员 | qwen-flash | 检查类任务，flash 足够 |
| Memory 提取 | qwen-flash | 结构化提取，flash 精准且便宜 |
| 深度质量评估 | qwen-flash | 评估类任务 |

### 5.5 特征开关 (Feature Flags)

所有新功能通过环境变量开关控制，支持灰度启用:

```python
ENABLE_RESEARCH_MEMORY: bool = True    # Phase 1
ENABLE_REFLECTION: bool = True         # Phase 2
ENABLE_THREE_PHASE_LOOP: bool = True   # Phase 3
ENABLE_DEPTH_QUALITY: bool = True      # Phase 5
```

**向后兼容**: 所有开关关闭时，Agent 回退到传统行为。

---

## 6. 部署与运维

### 6.1 服务器配置

- **IP**: 47.93.253.208
- **域名**: mmaoresearch.com
- **服务端口**: 8001
- **反向代理**: Nginx
- **进程管理**: systemd
- **SSL**: Let's Encrypt (certbot)

### 6.2 部署目录结构

```
/opt/mirothinker/
├── backend/
│   ├── src/              # Python 源代码
│   ├── data/
│   │   ├── logs/         # 日志文件
│   │   ├── cache/        # 搜索缓存
│   │   └── traces/       # 执行追踪
│   └── requirements.txt
├── frontend/             # 静态前端
├── .env                  # 环境变量
└── nginx.conf            # Nginx 配置
```

### 6.3 systemd 服务

```ini
[Unit]
Description=MiroThinker Deep Research Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/mirothinker/backend
EnvironmentFile=/opt/mirothinker/.env
ExecStart=/opt/miniconda/envs/mirothinker/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --workers 1 --log-level info
ExecStop=/bin/kill -TERM $MAINPID
Restart=always
RestartSec=5
MemoryHigh=384M
MemoryMax=512M

[Install]
WantedBy=multi-user.target
```

### 6.4 Nginx 配置

```nginx
upstream mirothinker_backend {
    server 127.0.0.1:8001;
    keepalive 32;
}

server {
    listen 80;
    server_name mmaoresearch.com www.mmaoresearch.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mmaoresearch.com www.mmaoresearch.com;

    ssl_certificate /etc/letsencrypt/live/mmaoresearch.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mmaoresearch.com/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://mirothinker_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 6.5 运维命令

```bash
# 查看服务状态
systemctl status mirothinker.service

# 重启服务
systemctl restart mirothinker.service

# 查看日志
journalctl -u mirothinker.service -f

# 测试健康检查
curl https://mmaoresearch.com/api/health

# 更新 SSL 证书
certbot renew
```

---

## 7. 成本分析

### 7.1 模型定价 (阿里云百炼)

| 模型 | 输入价格 | 输出价格 |
|------|---------|---------|
| qwen-turbo | 0.5 元/百万 tokens | 2 元/百万 tokens |
| qwen-plus | 2 元/百万 tokens | 8 元/百万 tokens |
| qwen3.6-plus | 10 元/百万 tokens | 30 元/百万 tokens |
| qwen-flash | 0.5 元/百万 tokens | 2 元/百万 tokens |

### 7.2 单次研究成本估算

**TIER_3 深度研究 (35轮)**:

| 阶段 | 模型 | 轮数 | 单次tokens | 小计 |
|------|------|------|-----------|------|
| Navigator | qwen-flash | 1 | 2,000 | 0.001 元 |
| 预搜索 | qwen-turbo | 1 | 3,000 | 0.002 元 |
| 搜索循环 | qwen-turbo | 25 | 15,000 | 0.375 元 |
| Memory提取 | qwen-flash | 25 | 1,000 | 0.013 元 |
| Reflection | qwen-flash | 5 | 3,000 | 0.008 元 |
| DepthQuality | qwen-flash | 3 | 5,000 | 0.008 元 |
| 综合 | qwen3.6-plus | 1 | 25,000 | 0.85 元 |
| 审查 | qwen-flash | 1 | 5,000 | 0.003 元 |
| **总计** | | | | **~1.26 元** |

### 7.3 月度成本估算

以百炼 ¥198/月套餐 (100K Credits ≈ 100 元等值):

| 使用强度 | 月请求数 | 月成本 |
|---------|---------|--------|
| 轻度 (TIER_1为主) | 2000 次 | ~100 元 |
| 中度 (混合 TIER) | 300 次 | ~100 元 |
| 重度 (TIER_3为主) | 80 次 | ~100 元 |

---

## 附录

### A. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-05-10 | 初始版本，基础多轮搜索 |
| 1.5 | 2026-05-11 | 质量系统、矛盾检测、信源评分 |
| 1.8 | 2026-05-14 | Token 优化、Navigator 路由、系统提示重构 |
| 2.0 | 2026-05-15 | 五阶段深度推理架构、动态方法论、会话持久化 |

### B. 文件清单

后端核心文件 (38 个 Python 文件):
- `src/main.py` — 应用入口
- `src/core/config.py` — 配置管理
- `src/core/session_store.py` — 会话持久化
- `src/core/task_store.py` — 任务存储
- `src/navigator/router.py` — 智能路由
- `src/navigator/budget_allocator.py` — 预算分配
- `src/services/agent.py` — Agent 主引擎
- `src/services/research_memory.py` — 结构化知识库
- `src/services/reflection.py` — 反思节点
- `src/services/depth_quality.py` — 深度质量评估
- `src/services/quality.py` — 质量系统
- `src/services/search.py` — 搜索与抓取
- `src/services/phases/planning.py` — 规划阶段
- `src/services/phases/deep_analysis.py` — 深度分析阶段
- `src/services/phases/synthesis.py` — 综合阶段
- `src/domains/{finance,tech,health,industry,policy,macro,general}.py` — 领域配置
- `src/routes/research.py` — 研究 API
- `src/routes/feishu.py` — 飞书 webhook
