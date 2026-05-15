# MiroThinker 项目全景与评审文档

> 版本: 2.0 (Post-Token-Optimization)
> 日期: 2026-05-15
> 用途: 全面技术评审与优化规划

---

## 目录

1. [项目总览](#1-项目总览)
2. [技术架构全景](#2-技术架构全景)
3. [核心能力模块](#3-核心能力模块)
4. [具体功能清单](#4-具体功能清单)
5. [领域系统详解](#5-领域系统详解)
6. [Token优化成果](#6-token优化成果)
7. [已知问题与优化机会](#7-已知问题与优化机会)

---

## 1. 项目总览

### 1.1 定位

MiroThinker 是一个面向复杂研究场景的自主 AI Agent 系统。核心特征:

- **深度 > 广度**: 多轮自主搜索(3~35轮)，聚焦单一问题的纵深分析
- **自主 > 引导**: Agent 自主决定搜索策略、信息来源、分析角度
- **质量 > 速度**: 多层质量检查 + 条件触发审查员机制
- **成本敏感**: 分层模型策略(qwen-turbo探索/qwen3.6-plus合成/qwen-flash分类)

### 1.2 技术栈

| 层级 | 技术 |
|-----|------|
| 后端框架 | FastAPI + Uvicorn + asyncio |
| LLM引擎 | 阿里云百炼 (DashScope) |
| 搜索工具 | DuckDuckGo (ddgs) + Trafilatura (零成本) |
| 可选搜索 | Serper API / Jina API |
| 持久化 | SQLite (任务存储) |
| 前端 | 原生 HTML/CSS/JS |
| 部署 | systemd + Linux 服务器 |
| 监控 | 结构化日志 + 健康检查端点 |

### 1.3 代码规模

- 后端 Python 代码: ~30个文件，核心逻辑约4000行
- 前端: 1个HTML + 1个JS + 1个CSS
- 领域配置: 6个领域模块 + 子类型系统
- 测试: pytest 测试套件

---

## 2. 技术架构全景

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      接入层 (API Layer)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ POST /research│  │ GET /status  │  │ GET /health      │  │
│  │ GET /research │  │ DELETE /...  │  │ Feishu Webhook   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      编排层 (Orchestration)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ResearchAgent.run() — 主循环             │  │
│  │  Navigator → Pre-search → Multi-turn Loop → Synthesis│  │
│  │  → Quality Check → Conditional Critic → Return       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  │
│  │ Task Store  │  │  Semaphore  │  │  AgentState        │  │
│  │  (SQLite)   │  │  (asyncio)  │  │ (context+dedup)    │  │
│  └─────────────┘  └─────────────┘  └────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      能力层 (Capability Layer)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Search  │  │  Domain  │  │ Quality  │  │  Critic  │  │
│  │  (ddgs)  │  │ Registry │  │ Pipeline │  │  Review  │  │
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
5. Pre-search 阶段
   - search_with_recency: 时效性感知搜索(近1月→近1年→通用)
   - 领域核心来源: DomainConfig.pre_search_strategy
   - 强制角度查询: mandatory_angle_queries
   - 结果上限: 10条(控制token)
        |
6. 自适应思维链组合 (compose_adaptive_chains)
   基础链(按tier过滤) + 子类型补充链 → 注入系统提示
        |
7. Agent 主循环 (while turn < max_turns)
   - 动态上下文窗口(基于信息饱和度自动缩减)
   - 分层模型: 搜索阶段qwen-turbo / 强制合成qwen3.6-plus
   - 工具解析: google_search / scrape_webpage (正则匹配)
   - ANTI-LOOP: Jaccard相似度去重 + 跨轮次查询记录
   - 智能早停: 连续无工具调用(3轮) / 来源饱和(25+)
   - 最小研究保护: <3轮且<3来源时拒绝 premature FINAL ANSWER
        |
8. 强制综合 (Max turns 或 FINAL ANSWER 触发)
   Focused Synthesis: 仅发送 system + query + 最近3条assistant + synthesis_prompt
   节省 ~2000-5000 tokens
        |
9. 质量检查 (QualityCheckPipeline)
   7项通用检查 + 领域特定检查 → overall_score
        |
10. 条件审查 (Conditional Critic)
    TIER_1: 跳过 | TIER_2: score<0.50触发 | TIER_3: score<0.70触发
    使用 qwen-flash, 高/中 severity 追加补充段落
        |
11. 更新任务状态 → SQLite
        |
12. 用户轮询获取结果 (GET /api/research/{task_id})
```

---

## 3. 核心能力模块

### 3.1 Navigator 智能路由 (`src/navigator/`)

**能力**: 单次LLM调用完成查询分类、预算分配、模型选择

| 组件 | 文件 | 功能 |
|-----|------|------|
| `navigate()` | `router.py` | 主入口: 分类→预算→模型选择→RoutingResult |
| `_classify_with_llm()` | `router.py` | qwen-flash调用, JSON解析, 验证tier/domain/subtype |
| `build_classify_prompt()` | `classify_prompt_builder.py` | 动态从DOMAIN_REGISTRY+SUBTYPE_CHAINS生成分类提示 |
| `allocate_budget()` | `budget_allocator.py` | 按tier分配max_turns/context_keep/system_tokens |
| `select_models()` | `budget_allocator.py` | 按tier选择search/synthesis/critic模型 |

**TIER配置**:

| Tier | max_turns | context_keep | search_model | synthesis_model | critic |
|------|-----------|--------------|--------------|-----------------|--------|
| TIER_1 | 8 | 2 | qwen-turbo | qwen-plus | 无 |
| TIER_2 | 20 | 3 | qwen-turbo | qwen3.6-plus | qwen-flash |
| TIER_3 | 35 | 4 | qwen-turbo | qwen3.6-plus | qwen-flash |

### 3.2 Agent 核心引擎 (`src/services/agent.py`)

**能力**: 多轮自主研究循环，工具调用，上下文管理

| 类/函数 | 功能 |
|---------|------|
| `ResearchAgent` | 核心Agent类，整合所有能力模块 |
| `ResearchAgent.run()` | 主执行入口: 路由处理→预搜索→循环→合成→质量→审查 |
| `ResearchAgent.call_llm()` | DashScope API封装，180s超时，token用量日志 |
| `ResearchAgent._pre_search()` | 预搜索阶段，返回最多10条基础结果 |
| `ResearchAgent._execute_tools()` | 解析工具调用(正则)，执行搜索/抓取 |
| `ResearchAgent._format_search_compact()` | 搜索结果单行压缩格式(标题\|链接\|摘要) |
| `ResearchAgent._critic_review()` | 审查员机制，qwen-flash执行盲点检查 |
| `ResearchAgent._parse_critic_response()` | 解析审查JSON响应 |
| `build_system_prompt()` | 构建系统提示(4段式: 核心指令+时间+领域链+输出格式) |
| `AgentState` | 对话状态管理 |
| `AgentState.add_message()` | 消息添加(assistant消息>300字符自动摘要) |
| `AgentState.get_context_window()` | 动态上下文窗口(去重+摘要+source汇总) |
| `AgentState.record_search()` | 记录搜索查询(去重用) |
| `AgentState.is_duplicate_search()` | Jaccard相似度>0.85判定重复 |

### 3.3 搜索与抓取 (`src/services/search.py`)

**能力**: 零成本搜索，时效性感知，结果缓存

| 类/函数 | 功能 |
|---------|------|
| `ToolClient` | 工具客户端，整合搜索+抓取+缓存 |
| `ToolClient.google_search()` | DuckDuckGo搜索，max_results=3，snippet=80字符 |
| `ToolClient.search_with_recency()` | 时效性搜索(近1月→财报专用→近1年→通用) |
| `ToolClient.scrape_webpage()` | Trafilatura抓取，返回400字符 |
| `SearchCache` | 内存缓存，1小时TTL，query+timelimit为key |
| `DateExtractor` | 从搜索结果提取日期(5种策略) |
| `DateExtractor.extract_from_result()` | 综合提取: snippet→title→URL |
| `DateExtractor._parse_text_for_date()` | 解析ISO/中文年月/相对日期/英文月份 |
| `DateExtractor._parse_url_for_date()` | 从URL路径解析日期 |

### 3.4 质量系统 (`src/services/quality.py`)

**能力**: 7维通用检查 + 领域特定检查 + 信源评分 + 矛盾检测

| 类/函数 | 功能 |
|---------|------|
| `QualityCheckPipeline` | 质量检查管道 |
| `QualityCheckPipeline.run()` | 执行通用+领域检查，返回overall_score |
| `_check_source_count()` | 来源数量检查(目标≥10) |
| `_check_citation_completeness()` | 引用完整性(含年份比例) |
| `_check_data_support()` | 数据支撑密度(数字密度) |
| `_check_temporal_consistency()` | 时间一致性(未来年份检测/时间悖论/来源老化) |
| `_check_contradictions()` | 矛盾处理标注检查 |
| `_check_structure()` | 结构完整性(4逻辑段+标题加分+表格加分) |
| `_check_language_quality()` | 语言质量(句长+过渡词) |
| `SourceCredibilityScorer` | 信源可信度评分器 |
| `SourceCredibilityScorer.score()` | 综合评分: 基础权重40%+内容30%+时效15%+引用15% |
| `SourceCredibilityScorer._evaluate_recency()` | 时效评分(支持部分日期+置信度折扣) |
| `ContradictionDetector` | 矛盾检测器 |
| `ContradictionDetector.detect()` | 按主题分组，检测数值/定性矛盾 |
| `ContradictionDetector._detect_numeric_conflicts()` | 同单位数值差异>20% |
| `ContradictionDetector._detect_qualitative_conflicts()` | 反义词对检测 |
| `FixedChannelSearch` | 固定渠道搜索(按L1/L2/L3优先级) |

### 3.5 领域系统 (`src/domains/`)

**能力**: 6大领域，19个子类型，动态LLM分类

| 组件 | 文件 | 功能 |
|-----|------|------|
| `DomainConfig` | `base.py` | 领域配置基类(思维链/搜索策略/质量检查/审查模板/输出格式) |
| `ThinkingChainDirective` | `base.py` | 思维链指令(章节级研究指导) |
| `SearchDirective` | `base.py` | 搜索指令(查询模板+目的+fallback) |
| `PreSearchStrategy` | `base.py` | 预搜索策略(强制角度+核心来源) |
| `format_thinking_chain()` | `base.py` | 思维链渲染为 ultra-compact 格式(节省70%token) |
| `select_thinking_chains()` | `base.py` | 按tier筛选思维链(T1无/T2关键/T3全部) |
| `DOMAIN_REGISTRY` | `registry.py` | 领域注册表(finance/tech/health/general/industry/policy/macro) |
| `register_domain()` | `registry.py` | 动态注册新领域 |
| `get_domain_config()` | `registry.py` | 获取领域配置 |
| `SUBTYPE_CHAINS` | `subtypes.py` | 子类型补充链注册表(19个子类型) |
| `compose_adaptive_chains()` | `adaptor.py` | 自适应组合基础链+子类型链 |
| `format_pivot_rules()` | `adaptor.py` | 子类型关键规则格式化 |

### 3.6 任务持久化 (`src/core/task_store.py`)

**能力**: SQLite持久化，跨重启恢复

| 函数 | 功能 |
|------|------|
| `create_task()` | 创建pending任务 |
| `get_task()` | 按ID查询，JSON反序列化 |
| `update_task()` | 增量更新，自动序列化JSON字段 |
| `list_tasks()` | 列表查询，支持状态筛选 |
| `cleanup_old_tasks()` | 清理过期任务(默认24h) |

### 3.7 前端界面 (`frontend/`)

**能力**: 纯静态页面，localStorage会话管理

| 组件 | 功能 |
|------|------|
| `index.html` | 响应式布局，侧边栏会话列表，主内容区 |
| `app.js` | 状态管理、表单提交、轮询、Markdown渲染、追问 |
| `renderMarkdown()` | 自定义Markdown解析(表格/代码/列表/引用) |
| `handleFollowUp()` | 追问功能(附加上下文启动新研究) |
| `loadConversations()` | localStorage加载+卡死修复 |

---

## 4. 具体功能清单

### 4.1 API 端点

| 方法 | 端点 | 功能 | 响应模型 |
|------|------|------|---------|
| POST | `/api/research` | 创建研究任务 | TaskResponse |
| GET | `/api/research/{task_id}` | 查询任务状态 | TaskResponse |
| DELETE | `/api/research/{task_id}` | 取消任务 | JSON |
| GET | `/api/health` | 健康检查 | JSON |
| GET | `/api/status` | 系统状态 | JSON |
| POST | `/api/v1/feishu/webhook` | 飞书Webhook | JSON |

### 4.2 Agent 循环阶段

| 阶段 | 触发条件 | 模型 | Token优化措施 |
|------|---------|------|--------------|
| Navigator分类 | 任务启动 | qwen-flash | 单次调用替代多次 |
| Pre-search | 分类完成后 | - | 结果上限10条 |
| 搜索轮次 | 每轮循环 | qwen-turbo | 上下文压缩、assistant摘要 |
| 强制合成 | 最后一轮或>=30轮 | qwen3.6-plus | Focused Synthesis(仅4条消息) |
| 质量检查 | 产出FINAL ANSWER后 | 本地代码 | 无LLM调用 |
| Critic审查 | quality_score<阈值 | qwen-flash | 条件触发(非每次都调) |

### 4.3 质量检查项 (7项通用 + N项领域)

**通用检查**:
1. 来源数量 (目标≥10)
2. 引用完整性 (含日期比例)
3. 数据支撑密度
4. 时间一致性 (未来年份/时间悖论/来源老化)
5. 矛盾处理标注
6. 结构完整性 (4逻辑段)
7. 语言质量

**金融领域检查**:
8. 最新财报数据引用
9. 核心议题识别与深度分析
10. 定性分析维度(业务/产业/战略/技术)
11. 数据时效性披露

### 4.4 ANTI-LOOP 机制 (三层)

| 层级 | 机制 | 实现 |
|------|------|------|
| L1 系统提示 | 明确禁止重复搜索 | core_directives: "结果相似则换关键词/语言/来源" |
| L2 代码检测 | Jaccard相似度去重 | `AgentState.is_duplicate_search()` |
| L3 警告注入 | 检测到循环时注入用户消息 | "WARNING: You just tried to search for something you already searched for" |

### 4.5 智能早停策略

| 条件 | 行为 |
|------|------|
| 连续3轮无工具调用 + sources>=5 | 提示提供FINAL ANSWER |
| 连续3轮无工具调用 + sources<5 | 强制要求继续搜索 |
| sources>=25 | 提示信息饱和，要求综合 |
| turn>=30 | 强制合成，系统提示追加URGENT |
| turn>=max_turns-1 | 最后一轮，执行工具后退出循环 |

---

## 5. 领域系统详解

### 5.1 已注册领域

| 领域 | 文件 | 思维链数 | 子类型数 | 质量检查 |
|------|------|---------|---------|---------|
| finance | `finance.py` | 6 | 6 | 4项 |
| tech | `tech.py` | 5 | 2 | 0 |
| health | `health.py` | 4 | 2 | 0 |
| general | `general.py` | 0 | 0 | 0 |
| industry | `industry.py` | - | 3 | 0 |
| policy | `policy.py` | - | 3 | 0 |
| macro | `macro.py` | - | 3 | 0 |

### 5.2 金融子类型 (6个)

| 子类型 | 分析重点 |
|--------|---------|
| concept_play | 概念炒作逻辑、资金结构、龙虎榜、持续性评估 |
| blue_chip | 护城河评估、股息率、股东回报、管理层配置 |
| turnaround | 退市风险、债务结构、重整方案、困境反转概率 |
| high_growth | TAM渗透率、产能扩张、增长质量(增收又增利) |
| sector_theme | 产业链图谱、板块龙头对比、景气周期 |
| macro_strategy | 宏观周期、货币政策、大类资产配置 |

### 5.3 输出模板 (压缩后)

所有领域的输出模板已从多行章节结构压缩为单行格式指令:

```
金融: "金融格式：最新信息/核心议题(2-4个)/财务数据/估值前景/风险结论。
      原则：自主决定重点，没找到最新财报继续搜，回答why+会怎样，附来源。"
```

---

## 6. Token优化成果

### 6.1 优化措施汇总

| 优化点 | 优化前 | 优化后 | 节省 |
|--------|--------|--------|------|
| 思维链格式 | 多行590字符/链 | 单行229字符/链 | 61% |
| 搜索结果数 | 5条 | 3条 | 40% |
| 结果snippet | 150字符 | 80字符 | 47% |
| 抓取内容 | 1500字符 | 400字符 | 73% |
| 工具结果上下文 | 1000字符 | 150字符 | 85% |
| 预搜索结果 | 20条 | 10条 | 50% |
| context_keep(T3) | 5 | 4 | 20% |
| context_keep(T2) | 4 | 3 | 25% |
| context_keep(T1) | 3 | 2 | 33% |
| 合成prompt | 多段落 | 单段落 | ~30% |
| assistant消息摘要 | 完整内容 | >300字符压缩为工具调用列表 | ~75% |

### 6.2 各阶段Token消耗估算

| 阶段 | 优化前 | 优化后 | 降幅 |
|------|--------|--------|------|
| 搜索阶段prompt | ~4300 | ~1329 | 69% |
| 搜索阶段completion | ~150 | ~150 | - |
| 合成阶段prompt | ~6000 | ~3000 | 50% |
| 上下文窗口(10轮后) | ~8000 | ~2000 | 75% |

### 6.3 关键Bug修复

- **模型停止调用工具**: 系统提示过度压缩导致模型忽略工具调用约束
  - 修复: 恢复强约束("强制搜索:每次回复必须先调用google_search()")
  - 修复: 明确格式示例 `google_search("query")`
  - 修复: assistant消息截断处理非工具调用消息

---

## 7. 已知问题与优化机会

### 7.1 当前已知问题

| # | 问题 | 影响 | 根因 |
|---|------|------|------|
| 1 | 模型重复相同搜索查询 | ANTI-LOOP频繁触发，有效搜索轮次减少 | assistant消息被过度摘要，历史上下文不足 |
| 2 | 自主搜索多样性有限 | 模型倾向于用相同关键词变体搜索 | 缺乏搜索策略指导(如语言切换/来源切换) |
| 3 | 来源去重逻辑问题 | context window去重时可能误删有用信息 | URL匹配不够精确，部分结果无URL |
| 4 | 追问功能未持久化 | 追问结果不存入SQLite | 追问通过前端附加上下文实现，后端无感知 |
| 5 | 前端token显示为模拟值 | meta-tokens显示不准确 | 后端未返回实际token_usage，前端硬编码默认值 |
| 6 | 飞书路由未纳入Navigator | 飞书消息不走完整的tier/domain分类 | feishu.py独立实现，未调用navigate() |
| 7 | 抓取工具使用频率低 | 模型很少调用scrape_webpage | 系统提示对抓取工具的引导不足 |
| 8 | 审查员触发阈值固定 | TIER_2阈值0.50可能过于宽松 | 未根据领域动态调整 |

### 7.2 高价值优化机会

#### A. 搜索策略增强 (高影响)

- **搜索建议生成器**: 在每轮后由LLM生成3个不同角度的搜索建议，注入下一轮上下文
- **语言切换引导**: 系统提示明确指导"中文结果不足时切换英文搜索"
- **来源轮换**: 记录已搜索的来源域名，提示切换新来源
- **子查询分解**: 将复杂查询自动分解为2-4个子查询并行搜索

#### B. 上下文管理优化 (高影响)

- **关键发现提取**: 每轮后由LLM提取关键发现(100字)，替代原始assistant消息
- **Source Memory**: 维护独立的高质量来源列表，不经过上下文窗口截断
- **动态context_keep**: 基于token用量实时调整，而非固定轮数

#### C. 模型策略优化 (中影响)

- **自适应模型切换**: 搜索初期用qwen-turbo，深度分析时自动升级
- **领域专用模型**: 金融用qwen-plus，技术用qwen3.6-plus(代码理解)
- **本地缓存LLM响应**: 对相同/相似查询的响应进行语义缓存

#### D. 质量系统增强 (中影响)

- **实时质量监控**: 每轮后计算中间质量分，质量下降趋势时提示调整策略
- **来源召回率检查**: 检查报告中引用的URL是否确实出现在搜索结果中
- **数值一致性检查**: 报告中的数值与原始来源比对

#### E. 工程优化 (低影响)

- **异步预搜索**: Navigator分类与预搜索并行执行
- **连接池复用**: httpx AsyncClient 在Agent生命周期内复用
- **前端SSE流式**: 用SSE替代轮询，减少请求数
- **Redis缓存**: 替换内存SearchCache为Redis，支持多实例

### 7.3 架构演进建议

```
当前: 单体FastAPI + 内存状态
建议: 服务化拆分

Phase 1 (短期):
  - 提取 Search Service (独立缓存/连接池)
  - 提取 Navigator Service (分类结果缓存)

Phase 2 (中期):
  - 引入消息队列(Celery/RQ)处理研究任务
  - 支持水平扩展多个worker

Phase 3 (长期):
  - 引入向量数据库存储研究记忆
  - 支持跨研究的增量知识积累
```

---

## 附录: 文件清单

### 后端核心文件

```
backend/src/
  main.py                      # FastAPI入口
  core/
    config.py                  # pydantic-settings配置
    logging_config.py          # 结构化日志
    task_store.py              # SQLite任务持久化
  routes/
    research.py                # 研究API路由
    feishu.py                  # 飞书Webhook
  services/
    agent.py                   # Agent核心引擎(~1180行)
    search.py                  # 搜索与抓取(~310行)
    quality.py                 # 质量系统(~550行)
  navigator/
    router.py                  # Navigator路由(~165行)
    budget_allocator.py        # 预算分配(~70行)
    classify_prompt_builder.py # 动态分类提示(~110行)
  domains/
    base.py                    # 领域基类(~135行)
    registry.py                # 领域注册表(~75行)
    adaptor.py                 # 自适应链组合(~80行)
    subtypes.py                # 子类型定义(~440行)
    finance.py                 # 金融领域配置
    tech.py                    # 技术领域配置
    health.py                  # 健康领域配置
    general.py                 # 通用领域配置
    industry.py                # 产业领域配置
    policy.py                  # 政策领域配置
    macro.py                   # 宏观领域配置
```

### 前端文件

```
frontend/
  index.html                   # 主页面
  js/app.js                    # 前端逻辑(~920行)
  css/style.css                # 样式
```

### 部署文件

```
scripts/
  setup.sh                     # 环境初始化
  deploy.sh                    # 生产部署
  start.sh                     # 服务启动
Dockerfile
docker-compose.yml
docker-compose.prod.yml
systemd/mirothinker.service
```
