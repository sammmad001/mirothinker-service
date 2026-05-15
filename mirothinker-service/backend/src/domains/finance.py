"""
MiroThinker - Finance Domain Configuration (v2)

Redesigned for flexible, adaptive analysis:
- Self-directed key issue identification (not rigid framework)
- Earnings/quarterly report recency priority
- Qualitative over quantitative: logic, industry, technology, operations
- Continuous search until latest info is found
"""

import re
from src.domains.base import (
    DomainConfig,
    ThinkingChainDirective,
    SearchDirective,
    SourceSearchTemplate,
    PreSearchStrategy,
)


# === 5 Adaptive Finance Thinking Chains ===
# Reduced from 11 rigid chains to 5 flexible ones.
# The agent is instructed to identify key issues dynamically,
# not mechanically follow all sections.

FINANCE_THINKING_CHAINS = [
    ThinkingChainDirective(
        section_id="fin_01_latest_intel",
        section_title="一、最新信息确认",
        section_order=1,
        importance="critical",
        search_directives=[
            SearchDirective(
                "{query} 最新财报 季度报告 {current_year}",
                "获取最新已发布的季度/年度财报",
                fallback_queries=[
                    "{query} {current_year} 年报 业绩",
                    "{query} 最新业绩公告",
                    "{query} quarterly earnings {current_year}",
                ],
            ),
            SearchDirective(
                "{query} 最新公告 重大事项 {current_year}",
                "获取最新公司公告和重大事件",
                fallback_queries=[
                    "{query} 最新动态 新闻",
                    "{query} 投资者关系 最新",
                ],
            ),
            SearchDirective(
                "{query} 券商研报 最新 {current_year}",
                "获取最新券商分析观点",
                required=False,
            ),
        ],
        analysis_logic=[
            "确认当前日期和最新财报发布时间 — 如果财报已发布但搜索未找到，必须换关键词继续搜索",
            "明确最新财报的覆盖期间（如2026年Q1），标注发布日期",
            "如果搜索未返回最新财报，标注'未找到最新财报'并说明可能原因（未发布/搜索限制）",
            "列出已确认的最新重大事件/公告时间线",
        ],
        verification_rules=[
            "财报数据必须标注报告期（如2026年Q1）和发布日期",
            "如果搜索返回的是旧财报，必须明确标注并继续搜索最新",
            "所有关键数据必须注明来源和时间",
        ],
        pitfall_warnings=[
            "不能使用过期财报数据而不加说明",
            "不能假设最新财报已发布/未发布，必须搜索确认",
            "不能因为没有找到就跳过最新信息分析",
        ],
        output_template=(
            "### 最新信息确认\n"
            "- 当前日期: [日期]\n"
            "- 最新财报: [报告期] | 发布日期: [日期] | 来源: [来源]\n"
            "- 若未找到最新财报: [说明原因及搜索尝试]\n\n"
            "### 最新重大事件时间线\n"
            "| 日期 | 事件 | 影响方向 |\n"
            "|------|------|---------|"
        ),
    ),
    ThinkingChainDirective(
        section_id="fin_02_key_issues",
        section_title="二、核心议题识别与深度分析",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective(
                "{query} 核心业务 经营分析 增长点",
                "了解当前最核心的经营议题",
            ),
            SearchDirective(
                "{query} 利润 盈利 亏损 原因分析",
                "深入分析利润变化的真实原因",
                fallback_queries=[
                    "{query} 净利润下滑 原因",
                    "{query} 盈利能力 变化",
                ],
            ),
            SearchDirective(
                "{query} 业务板块 分业务 收入结构",
                "了解各业务板块表现和变化",
                fallback_queries=[
                    "{query} 分部业绩 各业务",
                    "{query} segment revenue breakdown",
                ],
            ),
        ],
        analysis_logic=[
            "基于最新信息和搜索结果，自主识别2-4个最核心的分析议题（不要预设方向）",
            "对每个核心议题进行'为什么'和'会怎样'的深度分析：",
            "  - 议题1: 利润变化的真实原因（业务层面+宏观层面）",
            "  - 议题2: 核心业务/新兴业务的竞争态势和成长逻辑",
            "  - 议题3: 管理层战略调整及其效果（如适用）",
            "  - 议题4: 行业技术变革对公司的影响（如适用）",
            "分析必须结合产业逻辑、技术趋势、经营策略，不能只是数字对比",
            "对于利润下滑/亏损，必须拆解：哪个业务拖后腿？成本端还是收入端？是否一次性因素？",
            "对于未来修复/增长路径，必须给出可验证的判断依据和时间预期",
        ],
        verification_rules=[
            "每个核心议题必须有搜索数据或公告支撑",
            "利润变化分析必须拆解到业务单元层面，不能笼统归因",
            "对未来判断必须标注不确定性程度（高/中/低）",
        ],
        pitfall_warnings=[
            "不要机械罗列所有业务板块数据 — 只深入分析最关键的2-4个议题",
            "不要把财务数字变化当作原因 — 必须追问背后的经营逻辑",
            "不要只分析历史，要对未来走向给出判断（即使不确定也要说明）",
        ],
        output_template=(
            "### 核心议题识别\n"
            "基于最新信息，本次分析聚焦以下N个核心议题（自主判断，不机械套用）：\n"
            "1. [议题1名称]: [一句话说明为什么这是核心议题]\n"
            "2. [议题2名称]: [...]\n\n"
            "### 议题深度分析\n"
            "#### 议题1: [名称]\n"
            "**现状**: [...]\n"
            "**深层原因**: [经营/产业/技术/管理层面的逻辑分析，不是数字罗列]\n"
            "**未来走向**: [会怎样 + 判断依据 + 不确定性]\n\n"
            "#### 议题2: [名称]\n"
            "..."
        ),
    ),
    ThinkingChainDirective(
        section_id="fin_03_financial_quality",
        section_title="三、财务数据与质量",
        section_order=3,
        importance="important",
        search_directives=[
            SearchDirective(
                "{query} 财务数据 营收 净利润 毛利率 {current_year}",
                "获取关键财务数据",
            ),
            SearchDirective(
                "{query} 现金流 经营现金流 自由现金流",
                "验证利润质量",
            ),
            SearchDirective(
                "{query} 资产负债表 负债 资产结构",
                "检查财务健康度",
                required=False,
            ),
        ],
        analysis_logic=[
            "只呈现支撑核心议题分析的关键财务数据，不要罗列所有指标",
            "重点分析：利润质量（经营现金流/净利润比值）、收入真实性（应收增速 vs 营收增速）",
            "财务数据必须与核心议题挂钩 — 如利润下滑，用数据证明是成本问题还是收入问题",
            "3年趋势即可，不需要5年",
        ],
        verification_rules=[
            "财务数据必须标注报告期",
            "异常指标必须解释原因",
        ],
        pitfall_warnings=[
            "不要罗列无关的财务指标",
            "不要只列数字不解释含义",
        ],
        output_template=(
            "### 关键财务数据（支撑核心议题）\n"
            "| 指标 | [上期] | [本期] | 变化 | 与议题关联 |\n"
            "|------|--------|--------|------|-----------|\n\n"
            "### 利润质量评估\n"
            "- 经营现金流/净利润: [比值] | 质量: [高/中/低]\n"
            "- 异常项说明: [...]"
        ),
    ),
    ThinkingChainDirective(
        section_id="fin_04_valuation_outlook",
        section_title="四、估值与前景",
        section_order=4,
        importance="important",
        search_directives=[
            SearchDirective(
                "{query} 估值 PE PB 目标价 券商",
                "获取当前估值水平和机构观点",
            ),
            SearchDirective(
                "{query} 同业对比 可比公司 估值",
                "同业估值对比",
                required=False,
            ),
        ],
        analysis_logic=[
            "结合核心议题分析给出估值判断 — 如利润修复预期如何影响估值",
            "估值分析要简洁：当前估值水平 + 与历史/同业对比 + 核心议题对估值的潜在影响",
            "给出中性情景下的目标区间，标注关键假设",
        ],
        verification_rules=[
            "估值判断必须与核心议题分析一致",
            "必须标注估值假设",
        ],
        pitfall_warnings=[
            "不要罗列多种估值方法 — 选择最相关的1-2种即可",
            "估值不能脱离核心议题分析",
        ],
        output_template=(
            "### 估值分析\n"
            "- 当前PE/PB: [数值] | 历史分位: [高/中/低] | 同业对比: [溢价/折价]\n"
            "- 核心议题对估值影响: [分析]\n\n"
            "### 前景判断\n"
            "- 中性情景: [判断 + 时间预期]\n"
            "- 关键变量: [影响最大1-2个因素]"
        ),
    ),
    ThinkingChainDirective(
        section_id="fin_05_risk_conclusion",
        section_title="五、风险与结论",
        section_order=5,
        importance="important",
        search_directives=[
            SearchDirective(
                "{query} 风险 争议 诉讼 监管",
                "识别主要风险",
                required=False,
            ),
        ],
        analysis_logic=[
            "总结2-3条最关键的风险（与核心议题直接相关）",
            "给出3-5条核心结论，每条必须基于前面的分析",
            "结论要回答用户原始问题的核心关切",
        ],
        verification_rules=[
            "风险必须与核心议题相关，不能泛泛而谈",
            "结论必须有分析支撑",
        ],
        pitfall_warnings=[
            "不要列10条风险 — 只保留最关键的2-3条",
            "结论不能与分析脱节",
        ],
        output_template=(
            "### 核心风险\n"
            "1. [风险]: [影响程度高/中/低] | [与哪个核心议题相关]\n\n"
            "### 核心结论\n"
            "1. [...]\n"
            "2. [...]\n\n"
            "### 回答用户关切\n"
            "[直接回应用户原始问题的核心关切]"
        ),
    ),
]


# === Enhanced Pre-Search Strategy ===
# Key changes:
# 1. Added earnings/quarterly report specific searches
# 2. Added "latest" angle with current year/month
# 3. Added segment/business unit searches
# 4. Source templates prioritize financial data sources

FINANCE_PRE_SEARCH_STRATEGY = PreSearchStrategy(
    mandatory_angle_queries=[
        # Latest earnings/financial reports
        "{query} 最新财报 季度报告 {current_year}",
        "{query} 业绩 盈利 亏损 {current_year}",
        # Core business dynamics
        "{query} 业务 经营 最新动态 {current_year}",
        # Contrarian view
        "{query} 争议 风险 问题 {current_year}",
    ],
    source_search_templates=[
        # A股/港股财报权威来源
        SourceSearchTemplate(
            name="巨潮资讯(公告)",
            query_template="site:cninfo.com.cn {query} 公告",
            priority="highest",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="东方财富(财报)",
            query_template="site:eastmoney.com {query} 财报 业绩",
            priority="highest",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="同花顺(研报)",
            query_template="site:10jqka.com.cn {query} 研报 分析",
            priority="high",
            max_results=3,
        ),
        # International financial sources
        SourceSearchTemplate(
            name="新浪财经",
            query_template="site:finance.sina.com.cn {query} 财报",
            priority="high",
            max_results=3,
        ),
        # News for recent events
        SourceSearchTemplate(
            name="财经新闻",
            query_template="site:caixin.com OR site:ftchinese.com OR site:wallstreetcn.com {query}",
            priority="high",
            max_results=3,
        ),
    ],
    recency_preference="y",
)


# === Finance Quality Checks (simplified) ===

def check_finance_latest_data(result: str, metadata: dict) -> dict:
    """Check if the analysis uses latest available financial data."""
    issues = []
    score = 0.0

    # Check if current year/quarter is mentioned
    current_year = str(datetime.now().year)
    has_latest_year = current_year in result

    # Check if quarterly report is referenced
    has_quarterly = bool(re.search(r'Q[1-4]|季度|季报', result))

    # Check if earnings/业绩 is discussed
    has_earnings = bool(re.search(r'财报|业绩|earnings|revenue|profit', result, re.IGNORECASE))

    if has_latest_year and has_earnings:
        score = 1.0
    elif has_earnings:
        score = 0.6
        issues.append("分析了业绩但未明确标注是否为最新财报数据")
    else:
        score = 0.0
        issues.append("CRITICAL: 未找到对最新财报/业绩的分析")

    if not has_quarterly:
        issues.append("未引用季度报告数据")

    return {"score": score, "issues": issues}


def check_finance_key_issues(result: str, metadata: dict) -> dict:
    """Check if analysis identifies and deeply analyzes key issues."""
    issues = []
    score = 0.0

    # Check for self-identified key issues section (expanded synonyms)
    has_key_issues = bool(re.search(
        r'核心议题|关键议题|核心问题|关键发现|核心观点|主要问题|关键风险|核心矛盾|key issues|key findings|core issues',
        result, re.IGNORECASE
    ))

    # Check for deep causal analysis (not just data listing)
    has_why = bool(re.search(
        r'为什么|原因|逻辑|背后|驱动因素|归因|根源|机理|动因|深层|underlying|driver|归因|缘由|due to|because',
        result, re.IGNORECASE
    ))

    # Check for forward-looking / predictive analysis
    has_future = bool(re.search(
        r'会怎样|未来|展望|预期|走向|前瞻|预判|趋势|前景|预测|预计|潜在|风险展望|outlook|forecast|projection|forward',
        result, re.IGNORECASE
    ))

    if has_key_issues and has_why and has_future:
        score = 1.0
    elif has_why and has_future:
        score = 0.8  # Increased from 0.7 — causal + forward is still strong depth
        issues.append("有深度分析但未明确标识核心议题")
    elif has_why or has_future:
        score = 0.5  # Increased from 0.4 — partial depth is better than pure listing
        issues.append("分析深度尚可：建议同时补充因果分析与前瞻判断")
    else:
        score = 0.2  # Increased from 0.0 — give minimal credit for any analysis text
        issues.append("分析深度不足：缺少因果解释或前瞻性判断，建议超越数据罗列")

    return {"score": score, "issues": issues}


def check_finance_qualitative_depth(result: str, metadata: dict) -> dict:
    """Check if analysis goes beyond numbers to logic/strategy/industry."""
    issues = []
    score = 0.0

    # Check for qualitative analysis dimensions
    dimensions = {
        "business": bool(re.search(r'业务|经营|商业模式|收入结构', result)),
        "industry": bool(re.search(r'行业|产业|竞争格局|市场', result)),
        "strategy": bool(re.search(r'战略|管理层|方向|调整|转型', result)),
        "technology": bool(re.search(r'技术|产品|创新|研发', result)),
    }

    found = sum(dimensions.values())
    if found >= 3:
        score = 1.0
    elif found == 2:
        score = 0.7
        issues.append(f"定性分析维度不够：仅覆盖{found}/4个维度（业务/产业/战略/技术）")
    elif found == 1:
        score = 0.3
        issues.append("定性分析严重不足：仅覆盖1个维度")
    else:
        score = 0.0
        issues.append("CRITICAL: 缺少定性分析 — 没有业务/产业/战略/技术维度的探讨")

    return {"score": score, "issues": issues, "dimensions_found": dimensions}


def check_finance_recency_disclosure(result: str, metadata: dict) -> dict:
    """Check if analysis discloses data recency status."""
    issues = []
    score = 0.0

    # Check if analysis acknowledges when latest data is unavailable
    has_recency_note = bool(re.search(r'最新|发布日期|报告期|截至', result))
    has_data_limitation = bool(re.search(r'未找到|数据截止|数据有限|未能获取', result))

    if has_recency_note:
        score = 1.0
    elif has_data_limitation:
        score = 0.8
        issues.append("已说明数据限制但未标注具体时间")
    else:
        score = 0.3
        issues.append("未标注数据来源时间和时效性")

    return {"score": score, "issues": issues}


FINANCE_QUALITY_CHECKS = [
    check_finance_latest_data,
    check_finance_key_issues,
    check_finance_qualitative_depth,
    check_finance_recency_disclosure,
]


# === Finance Critic Template ===

FINANCE_CRITIC_TEMPLATE = """1. **时效性**：
   - 分析是否基于最新可获取的财报/公告？是否标注了数据时间？
   - 如果最新数据不可得，是否说明了原因？是否基于最新可用数据做了分析？
   - 是否遗漏了最近发布的重大信息？

2. **分析深度（最关键）**：
   - 是否只是罗列数字，还是有"为什么"和"会怎样"的深度分析？
   - 是否识别了最核心的2-4个议题并深入分析？
   - 分析是否结合了产业逻辑、技术趋势、经营策略？
   - 对于利润变化，是否拆解到了业务单元层面？

3. **定性维度**：
   - 是否覆盖了业务经营层面的分析？
   - 是否讨论了产业竞争格局和技术变革？
   - 是否涉及管理层战略和执行力？
   - 是否不只是财务指标对比？"""


# === Finance Output Template ===

FINANCE_OUTPUT_TEMPLATE = """金融格式：最新信息/核心议题(2-4个)/财务数据/估值前景/风险结论。原则：自主决定重点，没找到最新财报继续搜，回答why+会怎样，附来源。"""


# === Finance Domain Config ===

# Import datetime for quality checks
from datetime import datetime

# === Finance Analysis Methodology (Phase 4) ===

FINANCE_ANALYSIS_METHODOLOGY = """金融分析的核心是因果推导，不是数据罗列。

1.**财务归因链**:利润变化→哪个业务单元→什么驱动(量/价/成本/费用)→根因是什么
   - 示例:营收下滑→新能源车业务占比下降→补贴退坡导致低价车型需求萎缩→政策周期性影响
2.**竞争动态推导**:市场份额变化→竞争者行为→结构性因素→可持续性判断
3.**估值逻辑链**:当前估值水平→驱动因子→假设合理性→安全边际
4.**风险传导路径**:识别风险源→传导路径→影响范围→概率和量级
5.**预期差识别**:市场共识vs实际情况→偏差来源→修正方向

分析每个发现时追问:这说明了什么?为什么会这样?接下来会怎样?证据链是否完整?"""

finance_config = DomainConfig(
    name="金融/经济",
    keywords=[
        "经济", "金融", "GDP", "通胀", "投资", "股市", "市场", "A股", "概念股",
        "涨停", "重组", "转型", "公告", "财报", "股票", "基金", "债券", "利率",
        "汇率", "央行", "货币政策", "财政政策", "牛市", "熊市", "IPO", "上市公司",
        "估值", "PE", "PB", "DCF", "营收", "净利润", "ROE", "毛利率", "股息",
        "证券", "期货", "期权", "衍生品", "对冲", "杠杆", "融资", "并购", "收购",
        "stock", "investment", "finance", "market", "trading", "portfolio",
        "valuation", "earnings", "dividend", "bond", "equity", "IPO",
        "研报", "评级", "目标价", "买入", "卖出", "增持", "减持",
        "生态", "股份", "控股", "新材", "药业", "国际", "光电", "智能",
    ],
    thinking_chains=FINANCE_THINKING_CHAINS,
    pre_search_strategy=FINANCE_PRE_SEARCH_STRATEGY,
    quality_checks=FINANCE_QUALITY_CHECKS,
    critic_template=FINANCE_CRITIC_TEMPLATE,
    output_template=FINANCE_OUTPUT_TEMPLATE,
    max_directive_tokens=3000,
    analysis_methodology=FINANCE_ANALYSIS_METHODOLOGY,
)
