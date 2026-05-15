"""
MiroThinker - Macro Economy Analysis Domain Configuration

Thinking chains for macro economy analysis:
- Macro cycle positioning (GDP, PMI, CPI)
- Policy environment (monetary, fiscal, industrial)
- Asset class impact (stocks, bonds, commodities, FX)
- Outlook and risks (key variables, black swans)
"""

from src.domains.base import (
    DomainConfig,
    ThinkingChainDirective,
    SearchDirective,
    SourceSearchTemplate,
    PreSearchStrategy,
)


# === 4 Macro Thinking Chains ===

MACRO_THINKING_CHAINS = [
    ThinkingChainDirective(
        section_id="mac_01_cycle",
        section_title="一、宏观周期定位",
        section_order=1,
        importance="critical",
        search_directives=[
            SearchDirective("{query} GDP PMI CPI 信贷 社融 最新数据", "获取核心宏观数据"),
            SearchDirective("{query} 经济 周期 阶段 复苏 衰退", "判断周期位置"),
        ],
        analysis_logic=[
            "定位当前周期 — 复苏/扩张/滞胀/衰退，基于GDP增速+PMI+CPI组合",
            "分析关键指标趋势 — PMI方向、CPI压力、社融/信贷扩张/收缩",
            "判断周期转折信号 — 哪些指标在变化、方向是什么",
            "与历史周期对比 — 当前类似于哪段历史时期",
        ],
        verification_rules=[
            "宏观数据须标注来源、时间和口径",
            "周期判断须有≥3个指标交叉验证",
        ],
        pitfall_warnings=[
            "勿将单一指标当宏观趋势",
            "勿忽略数据修订和口径变化",
        ],
        output_template=(
            "### 周期定位\n"
            "| 指标 | 最新值 | 趋势 | 判断 |\n"
            "| GDP增速 | | | |\n"
            "| PMI | | | |\n"
            "| CPI | | | |\n"
            "| 社融 | | | |\n\n"
            "- 综合判断: 当前处于[周期阶段]"
        ),
    ),
    ThinkingChainDirective(
        section_id="mac_02_policy",
        section_title="二、政策环境分析",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 货币政策 利率 MLF LPR 降准", "分析货币政策"),
            SearchDirective("{query} 财政政策 资赤字 支出 减税", "分析财政政策"),
        ],
        analysis_logic=[
            "评估货币政策方向 — 宽松(降息降准)/中性/收紧",
            "评估财政政策方向 — 积极(扩赤字)/稳健/紧缩",
            "分析政策组合效应 — 货币+财政是否协调、矛盾在哪",
            "追踪政策信号 — 央行/财政部/发改委的最新表态",
        ],
        verification_rules=[
            "政策判断须有官方表态或数据支撑",
        ],
        pitfall_warnings=[
            "勿将政策表态等同于政策执行",
            "勿忽略政策的滞后效应",
        ],
        output_template=(
            "### 政策环境\n"
            "| 维度 | 方向 | 信号 | 效果评估 |\n"
            "| 货币政策 | 宽松/中性/收紧 | | |\n"
            "| 财政政策 | 积极/稳健/紧缩 | | |"
        ),
    ),
    ThinkingChainDirective(
        section_id="mac_03_assets",
        section_title="三、大类资产影响",
        section_order=3,
        importance="important",
        search_directives=[
            SearchDirective("{query} 股市 债市 商品 汇率 资产配置", "分析资产影响"),
            SearchDirective("{query} 行业 影响 受益 受损 配置建议", "搜索行业影响"),
        ],
        analysis_logic=[
            "分析各资产类别的预期表现 — 股/债/商品/汇率在当前环境下的方向",
            "识别受益/受损行业 — 宽松利好成长，收紧利好价值",
            "评估风险溢价变化 — 流动性扩张→风险偏好上升",
            "给出配置方向建议 — 但标注确定性等级",
        ],
        verification_rules=[
            "资产影响须有逻辑链条而非简单结论",
        ],
        pitfall_warnings=[
            "勿将宏观判断直接等同于投资建议",
            "勿忽略市场预期vs实际政策的偏差",
        ],
        output_template=(
            "### 大类资产方向\n"
            "| 资产 | 方向 | 确定性 | 核心驱动 |\n"
            "| 股市 | | | |\n"
            "| 债市 | | | |\n"
            "| 商品 | | | |\n"
            "| 汇率 | | | |"
        ),
    ),
    ThinkingChainDirective(
        section_id="mac_04_outlook",
        section_title="四、前景与风险",
        section_order=4,
        importance="supplementary",
        search_directives=[
            SearchDirective("{query} 前景 预测 风险 黑天鹅 不确定性", "搜索前景和风险"),
        ],
        analysis_logic=[
            "提炼2-3个核心变量 — 哪些因素将决定经济走向",
            "列出黑天鹅/尾部风险 — 地缘/债务/疫情/技术冲击",
            "给出方向性判断 — 标注置信度(高/中/低)",
            "说明研究局限性 — 宏观预测的固有不确定性",
        ],
        verification_rules=[
            "风险因素须有具体案例或历史参照",
        ],
        pitfall_warnings=[
            "勿给出超出分析范围的高确定性预测",
        ],
        output_template=(
            "### 核心变量\n"
            "1. [变量] → 影响方向和程度\n\n"
            "### 风险矩阵\n"
            "| 风险 | 概率 | 影响 | 缓解 |\n\n"
            "### 综合判断\n"
            "- 方向: [结论] | 确定性: [等级]"
        ),
    ),
]


# === Macro Subtype Chains ===

MACRO_MONETARY_CHAINS = [
    ThinkingChainDirective(
        section_id="mac_mon_01",
        section_title="货币政策深度分析",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 央行 货币政策 利率 MLF LPR 最新", "追踪央行操作"),
            SearchDirective("{query} 流动性 M2 社融 信贷 数据", "分析流动性数据"),
        ],
        analysis_logic=[
            "追踪央行最新操作 — MLF/LPR/降准/公开市场操作",
            "分析流动性指标 — M2增速/社融/信贷的结构变化",
            "判断货币政策空间 — 还有多少降息/降准余地",
            "评估传导效率 — 资金是否有效流入实体经济",
        ],
        verification_rules=[
            "利率和M2数据须标注最新月份",
        ],
        pitfall_warnings=[
            "勿忽略流动性陷阱风险",
        ],
        output_template=(
            "### 货币政策操作\n"
            "| 操作 | 日期 | 规模 | 效果 |\n\n"
            "### 流动性指标\n"
            "| 指标 | 最新值 | 上月 | 趋势 |"
        ),
    ),
]

MACRO_FISCAL_CHAINS = [
    ThinkingChainDirective(
        section_id="mac_fis_01",
        section_title="财政政策深度分析",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 资赤字 财政支出 减税 专项债", "分析财政数据"),
            SearchDirective("{query} 地方债务 隐性债务 风险", "评估地方债务"),
        ],
        analysis_logic=[
            "分析赤字规模和结构 — 中央vs地方、刚性vs弹性支出",
            "评估专项债发行 — 规模/投向/使用效率",
            "追踪减税降费效果 — 实际减负规模vs政策目标",
            "评估地方债务风险 — 隐性债务/偿债压力/违约风险",
        ],
        verification_rules=[
            "赤字数据须标注预算vs实际",
        ],
        pitfall_warnings=[
            "勿忽略隐性债务的真实规模",
        ],
        output_template=(
            "### 财政收支\n"
            "| 项目 | 规模 | 增速 | 占GDP |\n\n"
            "### 专项债\n"
            "- 发行规模 / 投向 / 使用进度"
        ),
    ),
]

MACRO_GLOBAL_CHAINS = [
    ThinkingChainDirective(
        section_id="mac_glo_01",
        section_title="全球宏观联动分析",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 全球 经济 美国 欧盟 联动 外溢", "分析全球联动"),
            SearchDirective("{query} 汇率 贸易 地缘 IMF 世行", "评估外部冲击"),
        ],
        analysis_logic=[
            "分析主要经济体周期差 — 美国vs中国vs欧洲的位置差异",
            "评估汇率影响 — 人民币/美元/欧元走势对国内的影响",
            "追踪贸易环境 — 关税/制裁/贸易协定变化",
            "分析地缘风险 — 军事冲突/制裁/能源供应中断",
        ],
        verification_rules=[
            "全球数据须标注国家和时间",
        ],
        pitfall_warnings=[
            "勿忽略全球溢出效应的传导路径",
        ],
        output_template=(
            "### 全球周期对比\n"
            "| 经济体 | 周期位置 | 货币政策 | 对中国影响 |\n\n"
            "### 外部风险\n"
            "| 风险 | 传导路径 | 概率 | 影响 |"
        ),
    ),
]


# === Macro Pre-Search Strategy ===

MACRO_PRE_SEARCH_STRATEGY = PreSearchStrategy(
    mandatory_angle_queries=[
        "{query} GDP PMI CPI 社融 最新数据 {current_year}",
        "{query} 政策 利率 货币 财政 最新表态",
    ],
    source_search_templates=[
        SourceSearchTemplate(
            name="央行数据",
            query_template="site:pbc.gov.cn {query} 货币政策 数据",
            priority="highest",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="统计局",
            query_template="site:stats.gov.cn {query} 数据 公报",
            priority="high",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="IMF/世行",
            query_template="site:imf.org OR site:worldbank.org {query} outlook",
            priority="medium",
            max_results=3,
        ),
    ],
    recency_preference="m",  # Monthly recency for macro data
)


# === Macro Critic Template ===

MACRO_CRITIC_TEMPLATE = """1. **数据时效性**：
   - 宏观数据是否是最最新的？是否标注了具体月份？
   - 是否区分了实际数据vs预测数据？
2. **周期判断准确性**：
   - 周期判断是否有≥3个指标交叉验证？
   - 是否考虑了数据修订的影响？
3. **政策分析深度**：
   - 是否区分了政策表态vs实际执行？
   - 是否考虑了政策的滞后效应？"""


# === Macro Output Template ===

MACRO_OUTPUT_TEMPLATE = """宏观格式：执行摘要/周期定位/政策环境/资产影响/前景风险。附数据来源和时间。"""


# === Macro Domain Config ===

# === Macro Analysis Methodology (Phase 4) ===

MACRO_ANALYSIS_METHODOLOGY = """宏观经济分析的核心是周期定位和传导机制推导，不是指标罗列。

1.**周期定位推导**:经济指标组合→当前周期位置(复苏/扩张/滞胀/衰退)→未来方向判断
2.**政策传导链**:货币政策/财政政策→金融市场→实体经济→居民部门→反馈循环
3.**跨市场联动**:利率→汇率→股市→债市→商品→房地产，跨市场传导路径
4.**领先-同步-滞后指标**:区分指标类型→预判趋势→验证判断→修正预期
5.**结构性vs周期性**:区分结构性变化和周期性波动，判断依据和投资含义

分析每个宏观发现时追问:这是领先还是滞后指标?传导机制是什么?历史类似情况结果如何?"""

macro_config = DomainConfig(
    name="宏观经济",
    keywords=["宏观", "GDP", "PMI", "CPI", "利率", "货币政策", "财政政策", "社融", "M2", "经济周期",
              "通胀", "通缩", "汇率", "资产配置", "降息", "降准"],
    thinking_chains=MACRO_THINKING_CHAINS,
    pre_search_strategy=MACRO_PRE_SEARCH_STRATEGY,
    quality_checks=[],  # Will add domain-specific checks later
    critic_template=MACRO_CRITIC_TEMPLATE,
    output_template=MACRO_OUTPUT_TEMPLATE,
    max_directive_tokens=2000,
    analysis_methodology=MACRO_ANALYSIS_METHODOLOGY,
)