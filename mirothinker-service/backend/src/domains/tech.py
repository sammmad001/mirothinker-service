"""
MiroThinker - Tech Domain Configuration

7 Thinking Chain Directives for technology analysis,
covering architecture, performance, ecosystem, and alternatives.
"""

import re
from src.domains.base import (
    DomainConfig,
    ThinkingChainDirective,
    SearchDirective,
    SourceSearchTemplate,
    PreSearchStrategy,
)


# === 7 Tech Thinking Chains ===

TECH_THINKING_CHAINS = [
    ThinkingChainDirective(
        section_id="tech_01_overview",
        section_title="一、技术概述",
        section_order=1,
        importance="critical",
        search_directives=[
            SearchDirective("{query} official documentation introduction", "获取官方核心概念"),
            SearchDirective("{query} what is overview 核心概念", "理解技术定位和核心价值"),
            SearchDirective("{query} 设计理念 架构原理 创新点", "理解设计哲学"),
        ],
        analysis_logic=[
            "识别核心技术架构模式（MVC/事件驱动/微服务/函数式等）",
            "提炼设计哲学和创新点 — 与同类技术的本质区别",
            "评估技术成熟度 — 是否有生产级应用案例",
            "确定适用场景 — 什么场景最适合、什么场景不合适",
        ],
        verification_rules=[
            "技术描述须与官方文档一致，不能凭印象",
            "适用场景声明须有实际案例支撑",
        ],
        pitfall_warnings=[
            "勿将营销话术当技术特性",
            "勿混淆'新'与'好' — 新技术不一定优于成熟技术",
            "勿忽略技术局限性 — 每种技术都有不适用场景",
        ],
        output_template=(
            "### 核心概念\n"
            "- 技术定位 + 核心价值\n\n"
            "### 设计哲学\n"
            "- 与同类技术的本质区别\n\n"
            "### 适用场景\n"
            "- 最适合 / 不适合的场景"
        ),
    ),
    ThinkingChainDirective(
        section_id="tech_02_architecture",
        section_title="二、架构与兼容性",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} architecture design 架构设计", "理解核心架构"),
            SearchDirective("{query} version compatibility breaking changes 版本兼容", "检查版本兼容风险"),
            SearchDirective("{query} migration guide upgrade 升级 迁移", "了解迁移路径和成本"),
        ],
        analysis_logic=[
            "绘制核心架构图 — 主要组件、数据流、依赖关系",
            "检查近3个大版本的向后兼容性 — 是否有破坏性变更",
            "评估迁移成本 — 从旧版本升级的难度和风险",
            "识别关键依赖 — 是否依赖特定操作系统/运行时/库版本",
        ],
        verification_rules=[
            "架构描述须与官方文档一致",
            "兼容性声明须标注具体版本号",
        ],
        pitfall_warnings=[
            "勿忽略破坏性变更（breaking changes）",
            "勿假设向后兼容 — 须验证",
            "勿忽略底层依赖的安全漏洞",
        ],
        output_template=(
            "### 核心架构\n"
            "- 主要组件 + 数据流 + 依赖关系\n\n"
            "### 版本兼容性\n"
            "| 版本 | 兼容性 | 破坏性变更 | 迁移难度 |\n"
            "|------|-------|----------|---------|\n\n"
            "### 关键依赖\n"
            "- 操作系统/运行时/核心库版本要求"
        ),
    ),
    ThinkingChainDirective(
        section_id="tech_03_performance",
        section_title="三、性能与基准",
        section_order=3,
        importance="critical",
        search_directives=[
            SearchDirective("{query} benchmark performance 性能 基准测试", "获取性能数据"),
            SearchDirective("{query} vs {alternative} benchmark comparison 对比", "对比替代方案性能"),
        ],
        analysis_logic=[
            "区分官方基准 vs 独立基准 — 官方基准往往选择最优场景",
            "评估真实世界性能 — 基准测试条件vs生产环境差异",
            "识别性能瓶颈 — 什么场景下性能下降明显",
            "性能与资源消耗权衡 — 吞吐量vs延迟vs内存消耗",
        ],
        verification_rules=[
            "性能声明须标注测试条件（硬件、数据集、并发数）",
            "须有独立第三方基准验证，不能只依赖官方数据",
        ],
        pitfall_warnings=[
            "勿只引用官方基准 — 须找独立验证",
            "勿忽略测试条件差异 — 不同条件下的结果不可直接比较",
            "勿将基准测试结果等同于生产环境表现",
        ],
        output_template=(
            "### 性能数据\n"
            "| 指标 | 官方基准 | 独立基准 | 生产环境预估 |\n"
            "|------|---------|---------|------------|\n\n"
            "### 性能瓶颈\n"
            "- 什么场景下性能下降\n\n"
            "### 与替代方案对比\n"
            "- 关键场景的性能差异"
        ),
    ),
    ThinkingChainDirective(
        section_id="tech_04_ecosystem",
        section_title="四、生态与社区",
        section_order=4,
        importance="important",
        search_directives=[
            SearchDirective("{query} ecosystem packages plugins 生态 插件", "了解生态丰富度"),
            SearchDirective("{query} github contributors stars issues", "评估社区活跃度"),
        ],
        analysis_logic=[
            "评估生态成熟度 — 包/插件数量、质量、维护状态",
            "社区活跃度 — 贡献者数量、Issue解决速度、Release频率",
            "商业支持 — 是否有企业版/付费支持/SLA保障",
            "学习资源 — 文档质量、教程数量、培训体系",
        ],
        verification_rules=[
            "GitHub数据须标注查看日期",
            "包/插件须检查是否仍在维护（最近更新时间）",
        ],
        pitfall_warnings=[
            "勿将'包数量'等同于'生态质量' — 很多包已废弃",
            "勿将'GitHub Stars'等同于'生产采用率'",
            "勿忽略社区分歧/分裂的信号（如Fork数量异常）",
        ],
        output_template=(
            "### 生态成熟度\n"
            "- 包/插件数量 + 质量 + 维护状态\n\n"
            "### 社区活跃度\n"
            "| 指标 | 数据 |\n"
            "|------|------|\n"
            "| 贡献者 | |\n"
            "| Stars | |\n"
            "| Issue解决中位时间 | |\n\n"
            "### 商业支持\n"
            "- 企业版/付费支持/SLA"
        ),
    ),
    ThinkingChainDirective(
        section_id="tech_05_alternatives",
        section_title="五、替代方案对比",
        section_order=5,
        importance="important",
        search_directives=[
            SearchDirective("{query} vs alternatives comparison 替代 对比", "识别替代方案"),
            SearchDirective("{query} competitors similar 代替方案 竞品", "了解竞品优劣势"),
        ],
        analysis_logic=[
            "建立特性对比矩阵 — 核心功能、性能、生态、学习曲线",
            "识别各自的最佳适用场景 — 没有万能技术",
            "评估迁移成本 — 从当前技术切换的难度",
            "市场趋势 — 哪个方向在获得更多采用",
        ],
        verification_rules=[
            "对比须基于客观标准（性能数据、功能列表），不是主观偏好",
            "每个替代方案须有实际使用经验或案例引用",
        ],
        pitfall_warnings=[
            "勿只对比优点 — 须客观列出缺点",
            "勿忽略小众但更适合特定场景的方案",
            "勿将个人偏好当客观评价",
        ],
        output_template=(
            "### 特性对比矩阵\n"
            "| 特性 | [本技术] | 替代A | 替代B |\n"
            "|------|---------|-------|-------|\n"
            "| 核心功能 | | | |\n"
            "| 性能 | | | |\n"
            "| 生态 | | | |\n"
            "| 学习曲线 | | | |\n\n"
            "### 各方案最佳场景\n"
            "- [本技术]: ...\n"
            "- [替代A]: ..."
        ),
    ),
    ThinkingChainDirective(
        section_id="tech_06_deprecation",
        section_title="六、版本迁移与废弃",
        section_order=6,
        importance="important",
        search_directives=[
            SearchDirective("{query} deprecated API migration 废弃 迁移", "识别废弃特性"),
            SearchDirective("{query} upgrade guide breaking changes 升级指南", "了解迁移路径"),
        ],
        analysis_logic=[
            "列出最近版本的废弃API/特性 — 及其替代方案",
            "评估迁移影响 — 涉及的代码范围和改动量",
            "识别技术债务 — 已废弃但仍被广泛使用的特性",
            "前瞻性评估 — 当前版本中可能在未来被废弃的模式",
        ],
        verification_rules=[
            "废弃声明须引用官方公告或Changelog",
            "迁移路径须可验证（是否有官方迁移工具/指南）",
        ],
        pitfall_warnings=[
            "勿忽略即将废弃的特性 — 提前规划迁移",
            "勿将废弃特性用于新项目",
        ],
        output_template=(
            "### 废弃特性\n"
            "| 特性 | 废弃版本 | 替代方案 | 迁移难度 |\n"
            "|------|---------|---------|---------|\n\n"
            "### 迁移建议\n"
            "- 推荐的迁移策略和优先级"
        ),
    ),
    ThinkingChainDirective(
        section_id="tech_07_conclusion",
        section_title="七、结论与建议",
        section_order=7,
        importance="supplementary",
        search_directives=[],
        analysis_logic=[
            "综合以上分析，给出适用场景评估",
            "明确推荐/不推荐的场景",
            "标注评估局限性 — 评估范围、时效性、深度",
        ],
        verification_rules=[
            "建议须与前面分析一致",
        ],
        pitfall_warnings=[
            "勿给出与前面分析矛盾的建议",
            "勿忽略技术选型的上下文（团队技能、项目规模等）",
        ],
        output_template=(
            "### 适用场景评估\n"
            "- 推荐场景 / 不推荐场景\n\n"
            "### 核心结论（3-5条）\n"
            "1. ...\n\n"
            "### 评估局限性\n"
            "- 评估范围 + 时效性"
        ),
    ),
]


# === Tech Pre-Search Strategy ===

TECH_PRE_SEARCH_STRATEGY = PreSearchStrategy(
    mandatory_angle_queries=[
        "{query} 最新 {current_year}",
        "{query} limitations criticisms 缺陷 争议",
        "{query} alternatives competitors 替代方案",
        "{query} deprecated breaking changes 废弃 兼容",
    ],
    source_search_templates=[
        SourceSearchTemplate(
            name="官方文档源",
            query_template="site:github.com OR site:docs.google.com OR site:readthedocs.io {query}",
            priority="highest",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="技术社区",
            query_template="site:stackoverflow.com OR site:dev.to OR site:medium.com {query}",
            priority="high",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="学术信源",
            query_template="site:arxiv.org OR site:scholar.google.com {query}",
            priority="medium",
            max_results=3,
        ),
    ],
    recency_preference="y",
)


# === Tech Quality Checks ===

def check_tech_version_compatibility(result: str, metadata: dict) -> dict:
    """Check if version numbers and compatibility are mentioned."""
    issues = []
    has_version = bool(re.search(r'v?\d+\.\d+|版本|version|release', result, re.IGNORECASE))
    has_compatibility = bool(re.search(r'兼容|兼容性|compatible|backward|breaking', result, re.IGNORECASE))

    if has_version and has_compatibility:
        return {"score": 1.0, "issues": []}
    elif has_version or has_compatibility:
        score = 0.5
        if not has_compatibility:
            issues.append("技术分析缺少版本兼容性说明")
        if not has_version:
            issues.append("技术分析缺少具体版本号引用")
        return {"score": score, "issues": issues}
    else:
        return {"score": 0.2, "issues": ["CRITICAL: 技术分析缺少版本号和兼容性信息"]}


def check_tech_alternative_comparison(result: str, metadata: dict) -> dict:
    """Check if alternatives are discussed."""
    has_alternatives = bool(re.search(r'替代|替代方案|vs|versus|alternative|比较|对比|竞品', result, re.IGNORECASE))
    if has_alternatives:
        return {"score": 1.0, "issues": []}
    return {"score": 0.3, "issues": ["技术分析缺少替代方案对比"]}


def check_tech_deprecation_warnings(result: str, metadata: dict) -> dict:
    """Check if deprecated features are flagged."""
    has_deprecation = bool(re.search(r'废弃|deprecated|过时|legacy|migrate|迁移', result, re.IGNORECASE))
    if has_deprecation:
        return {"score": 1.0, "issues": []}
    # Deprecation info is optional, so just flag as info
    return {"score": 0.6, "issues": ["建议标注已废弃的特性和迁移路径"]}


def check_tech_code_examples(result: str, metadata: dict) -> dict:
    """Check if code snippets or API references are present."""
    has_code = bool(re.search(r'```|`[^`]+`|API|接口|函数|method|class ', result))
    if has_code:
        return {"score": 1.0, "issues": []}
    return {"score": 0.5, "issues": ["技术分析建议包含代码示例或API引用"]}


TECH_QUALITY_CHECKS = [
    check_tech_version_compatibility,
    check_tech_alternative_comparison,
    check_tech_deprecation_warnings,
    check_tech_code_examples,
]


# === Tech Critic Template ===

TECH_CRITIC_TEMPLATE = """1. **视角完整性**：
   - 是否只呈现了技术优点，忽略了已知限制和缺陷？
   - 是否检查了API废弃和迁移路径？
   - 是否提供了与替代方案的客观对比？
   - 性能声明是否有独立基准测试支持？
   - 是否考虑了团队采用的学习曲线和迁移成本？"""


# === Tech Output Template ===

TECH_OUTPUT_TEMPLATE = """技术格式：概述/核心概念/对比分析/生态/风险/结论。用表格对比，附来源。"""


# === Tech Domain Config ===

# === Tech Analysis Methodology (Phase 4) ===

TECH_ANALYSIS_METHODOLOGY = """技术分析的核心是技术趋势推导和影响评估，不是功能罗列。

1.**技术成熟度判断**:理论→原型→试点→规模化→普及，当前处于哪一阶段？驱动和阻碍因素？
2.**技术因果链**:技术突破→产业影响→商业模式变化→竞争格局重塑
3.**生态位分析**:技术栈中的位置→依赖关系→替代风险→演进方向
4.**采用曲线推导**:早期采用者→跨越鸿沟→主流采纳，当前在曲线哪个位置？
5.**二阶效应**:技术普及后的间接影响—新市场/新风险/新依赖

分析每个技术发现时追问:这项技术的实际影响路径是什么?为什么现在而不是以前?什么条件下会加速/减速?"""

tech_config = DomainConfig(
    name="技术/科技",
    keywords=[
        "AI", "machine learning", "technology", "software", "computer",
        "算法", "人工智能", "技术", "算力", "GPU", "芯片", "编程",
        "框架", "开发", "API", "云计算", "大数据", "区块链", "物联网",
        "5G", "自动驾驶", "机器人", "数据库", "操作系统", "编程语言",
        "Python", "Java", "JavaScript", "Rust", "Go", "TypeScript",
        "React", "Vue", "Docker", "Kubernetes", "AWS", "Azure",
        "framework", "library", "tool", "platform", "architecture",
        # 常见AI/ML框架和工具名
        "PyTorch", "TensorFlow", "Keras", "Hugging Face", "LangChain",
        "OpenAI", "GPT", "LLM", "transformer", "deep learning",
        "深度学习", "机器学习", "模型", "训练", "推理", "部署",
        # 常见云/DevOps工具
        "GCP", "Terraform", "CI/CD", "Git", "Linux", "Nginx",
        # 技术分析行为词
        "benchmark", "性能", "兼容", "版本", "对比", "迁移",
    ],
    thinking_chains=TECH_THINKING_CHAINS,
    pre_search_strategy=TECH_PRE_SEARCH_STRATEGY,
    quality_checks=TECH_QUALITY_CHECKS,
    critic_template=TECH_CRITIC_TEMPLATE,
    output_template=TECH_OUTPUT_TEMPLATE,
    max_directive_tokens=2500,
    analysis_methodology=TECH_ANALYSIS_METHODOLOGY,
)
