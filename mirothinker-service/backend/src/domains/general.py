"""
MiroThinker - General Domain Configuration

5 Thinking Chain Directives for general-purpose research,
applicable when no specific domain is detected.
"""

from src.domains.base import (
    DomainConfig,
    ThinkingChainDirective,
    SearchDirective,
    SourceSearchTemplate,
    PreSearchStrategy,
)


# === 5 General Thinking Chains ===

GENERAL_THINKING_CHAINS = [
    ThinkingChainDirective(
        section_id="gen_01_summary",
        section_title="一、执行摘要",
        section_order=1,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 最新 {current_year}", "获取最新动态"),
            SearchDirective("{query} 概述 overview 总结", "获取基础概览"),
        ],
        analysis_logic=[
            "提炼2-3个核心发现 — 每个须有数据支撑",
            "标注信息确定性 — 已确认/有争议/待验证",
            "总结对读者的关键影响",
        ],
        verification_rules=[
            "核心发现须有具体数据或来源引用",
        ],
        pitfall_warnings=[
            "勿使用模糊描述 — 须用具体数字和时间",
        ],
        output_template=(
            "## 执行摘要\n"
            "- 2-3句话总结核心发现\n"
            "- 使用数据支撑关键结论"
        ),
    ),
    ThinkingChainDirective(
        section_id="gen_02_findings",
        section_title="二、关键发现",
        section_order=2,
        importance="important",
        search_directives=[
            SearchDirective("{query} 详细 分析 数据 统计", "获取详细数据"),
        ],
        analysis_logic=[
            "按主题组织发现 — 每个发现独立成节",
            "每个发现须有：数据点 + 来源 + 时间范围",
            "标注发现的置信度",
        ],
        verification_rules=[
            "每个关键声明须有至少1个来源引用",
        ],
        pitfall_warnings=[
            "勿将传闻当事实 — 须标注信息来源可靠性",
            "勿忽略矛盾信息 — 须呈现并解释",
        ],
        output_template=(
            "### 发现一：[分类标题]\n"
            "- 关键数据点（具体数字、百分比）\n"
            "- 来源 [来源名称]\n"
            "- 时间范围/趋势"
        ),
    ),
    ThinkingChainDirective(
        section_id="gen_03_debate",
        section_title="三、不同观点与争议",
        section_order=3,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 争议 不同观点 反对 批评", "搜索反对意见"),
            SearchDirective("{query} 变化 转型 趋势 新发展", "搜索新发展"),
        ],
        analysis_logic=[
            "呈现正反双方观点 — 每方至少2条论据",
            "评估各方证据的强度",
            "分析争议的根源 — 利益冲突/信息不对称/价值取向",
        ],
        verification_rules=[
            "反对意见须来自独立来源，不能只引用同一来源",
        ],
        pitfall_warnings=[
            "勿只呈现一方观点 — 必须有反对声音",
            "勿将'主流观点'等同于'正确观点'",
        ],
        output_template=(
            "## 不同观点与争议\n"
            "| 观点 | 支持论据 | 反对论据 | 可信度 |\n"
            "|------|---------|---------|--------|"
        ),
    ),
    ThinkingChainDirective(
        section_id="gen_04_trends",
        section_title="四、趋势与展望",
        section_order=4,
        importance="important",
        search_directives=[
            SearchDirective("{query} 趋势 未来 发展 前景", "了解未来方向"),
        ],
        analysis_logic=[
            "识别当前趋势方向 — 基于数据，非主观判断",
            "区分确定趋势vs推测 — 明确标注",
            "考虑二阶效应 — 直接后果之外的影响",
        ],
        verification_rules=[
            "趋势判断须有数据支撑（增速、渗透率等）",
        ],
        pitfall_warnings=[
            "勿将短期波动当长期趋势",
            "勿忽略黑天鹅事件的可能性",
        ],
        output_template=(
            "### 当前趋势\n"
            "- [基于数据描述]\n\n"
            "### 未来展望\n"
            "- 已确认趋势 / 推测方向（须标注）"
        ),
    ),
    ThinkingChainDirective(
        section_id="gen_05_conclusion",
        section_title="五、结论与建议",
        section_order=5,
        importance="supplementary",
        search_directives=[],
        analysis_logic=[
            "综合3-5条核心结论",
            "给出行动建议 — 但标注置信度",
            "说明研究局限性",
        ],
        verification_rules=[
            "结论须与前面分析一致",
        ],
        pitfall_warnings=[
            "勿给出超出分析范围的结论",
        ],
        output_template=(
            "## 结论与建议\n"
            "- 核心结论（3-5条）+ 行动建议 + 研究局限性\n\n"
            "## 参考资料\n"
            "1. [来源名称](URL) - 关键信息摘要"
        ),
    ),
]


# === General Pre-Search Strategy ===

GENERAL_PRE_SEARCH_STRATEGY = PreSearchStrategy(
    mandatory_angle_queries=[
        "{query} 最新 {current_year}",
        "{query} 争议 不同观点 反对",
    ],
    source_search_templates=[
        SourceSearchTemplate(
            name="新闻信源",
            query_template="site:reuters.com OR site:xinhuanet.com OR site:caixin.com {query}",
            priority="high",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="学术信源",
            query_template="site:scholar.google.com OR site:arxiv.org {query}",
            priority="medium",
            max_results=3,
        ),
    ],
    recency_preference="y",
)


# === General Critic Template ===

GENERAL_CRITIC_TEMPLATE = """1. **视角完整性**：
   - 是否只呈现了一种观点，忽略了争议或反对意见？
   - 是否遗漏了最新动态或重大事件？
   - 核心声明是否都有数据或来源支撑？
   - 是否考虑了二阶效应和间接影响？"""


# === General Output Template ===

GENERAL_OUTPUT_TEMPLATE = """通用格式：执行摘要/关键发现/详细分析/不同观点/结论建议/参考资料。用表格和数据，精简表述，每个关键声明附来源。"""


# === General Domain Config ===

# === General Analysis Methodology (Phase 4) ===

GENERAL_ANALYSIS_METHODOLOGY = """通用研究的核心是多角度因果推导，不是信息汇总。

1.**问题拆解**:将大问题分解为2-4个关键子问题，每个子问题独立分析
2.**因果推导**:对每个发现追问WHY至少两层—现象→直接原因→根本原因
3.**假设-验证循环**:形成初步假设→搜索支持/反对证据→修正假设→再验证
4.**多维交叉验证**:同一结论需要不同来源/角度/方法的支撑
5.**不确定性分级**:区分已确认事实、合理推测、有争议观点，不可混淆

分析每个发现时追问:为什么会这样?证据链是否完整?有没有其他解释?这个结论有多确定?"""

general_config = DomainConfig(
    name="通用研究",
    keywords=[],  # General is the fallback, no specific keywords
    thinking_chains=GENERAL_THINKING_CHAINS,
    pre_search_strategy=GENERAL_PRE_SEARCH_STRATEGY,
    quality_checks=[],  # No domain-specific checks for general
    critic_template=GENERAL_CRITIC_TEMPLATE,
    output_template=GENERAL_OUTPUT_TEMPLATE,
    max_directive_tokens=1500,
    analysis_methodology=GENERAL_ANALYSIS_METHODOLOGY,
)
