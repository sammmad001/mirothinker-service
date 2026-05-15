"""
MiroThinker - Policy/Regulation Analysis Domain Configuration

Thinking chains for policy/regulation analysis:
- Policy interpretation and background
- Impact scope and pathways
- Stakeholder analysis (beneficiaries, affected parties)
- Implementation outlook and risks
"""

from src.domains.base import (
    DomainConfig,
    ThinkingChainDirective,
    SearchDirective,
    SourceSearchTemplate,
    PreSearchStrategy,
)


# === 4 Policy Thinking Chains ===

POLICY_THINKING_CHAINS = [
    ThinkingChainDirective(
        section_id="pol_01_interpretation",
        section_title="一、政策解读与背景",
        section_order=1,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 政策原文 公告 通知 文件", "搜索政策原文"),
            SearchDirective("{query} 出台背景 原因 目的 目标群体", "了解政策背景"),
            SearchDirective("{query} 政策解读 分析 影响 专家观点", "获取专业解读"),
        ],
        analysis_logic=[
            "梳理政策核心内容 — 一句话总结政策意图",
            "分析出台背景 — 什么问题/痛点催生了该政策",
            "识别目标群体 — 政策针对哪些企业/行业/人群",
            "评估政策层级 — 中央/地方/行业，层级越高执行力越强",
        ],
        verification_rules=[
            "政策内容须引用原文，标注文号和发布日期",
            "解读须区分政策原文 vs 分析推测",
        ],
        pitfall_warnings=[
            "勿将媒体解读等同于政策原文",
            "勿忽略政策实施细则（通常比原文更重要）",
        ],
        output_template=(
            "### 政策概览\n"
            "| 维度 | 内容 |\n"
            "|------|------|\n"
            "| 文号 | [文号] |\n"
            "| 发布日期 | [日期] |\n"
            "| 核心意图 | [一句话] |\n"
            "| 目标群体 | [群体] |"
        ),
    ),
    ThinkingChainDirective(
        section_id="pol_02_impact",
        section_title="二、影响范围与路径",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 影响 受益 受损 行业 企业", "分析直接影响"),
            SearchDirective("{query} 间接影响 二阶效应 连带", "搜索间接影响"),
        ],
        analysis_logic=[
            "梳理影响路径 — 政策→直接影响→间接影响→二阶效应",
            "量化影响程度 — 对营收/利润/成本的具体影响估算",
            "区分短期vs长期影响 — 短期情绪 vs 中期实质 vs 长期格局",
            "分析地域差异 — 政策在不同地区的执行差异",
        ],
        verification_rules=[
            "影响判断须有具体逻辑链条",
            "区分已确认影响 vs 预测影响",
        ],
        pitfall_warnings=[
            "勿将政策出台等同于实际执行",
            "勿忽略政策的负面副作用",
        ],
        output_template=(
            "### 影响路径\n"
            "政策 → 直接影响 → 间接影响 → 二阶效应\n\n"
            "### 受益/受损方\n"
            "| 主体 | 影响类型 | 影响程度 | 时间维度 |"
        ),
    ),
    ThinkingChainDirective(
        section_id="pol_03_stakeholders",
        section_title="三、利益相关方分析",
        section_order=3,
        importance="important",
        search_directives=[
            SearchDirective("{query} 利益方 受益方 反对 执行者", "识别利益方"),
            SearchDirective("{query} 反应 争议 评价 反馈", "搜索各方反应"),
        ],
        analysis_logic=[
            "识别四类利益方 — 受益方/受损方/执行者/旁观者",
            "分析各方动机 — 利益驱动 vs 原则驱动",
            "评估博弈格局 — 支持力量 vs 反对力量的强弱",
            "预测博弈走向 — 政策会被强化/弱化/搁置/推翻？",
        ],
        verification_rules=[
            "利益方分析须有具体案例",
        ],
        pitfall_warnings=[
            "勿只看正面受益方，忽略受损方的反弹力量",
        ],
        output_template=(
            "### 利益方分析\n"
            "| 利益方 | 立场 | 动机 | 力量强弱 |"
        ),
    ),
    ThinkingChainDirective(
        section_id="pol_04_outlook",
        section_title="四、实施展望与风险",
        section_order=4,
        importance="supplementary",
        search_directives=[
            SearchDirective("{query} 执行 进度 落地 试点 案例", "追踪执行进度"),
        ],
        analysis_logic=[
            "评估执行难度 — 中央政策vs地方执行的落差",
            "追踪落地进度 — 已出台细则/已开始试点/全面执行",
            "识别潜在偏差 — 执行走样/选择性执行/过度执行",
            "预测时效性 — 政策有效期/调整窗口",
        ],
        verification_rules=[
            "执行进度须有事实依据",
        ],
        pitfall_warnings=[
            "勿假设政策100%按原文执行",
        ],
        output_template=(
            "### 实施进度\n"
            "- 细则出台: 是/否\n"
            "- 试点范围: [地域]\n"
            "- 执行进度: [百分比]\n\n"
            "### 风险提示\n"
            "1. [风险] — 概率: 高/中/低"
        ),
    ),
]


# === Policy Subtype Chains ===

POLICY_REGULATION_CHAINS = [
    ThinkingChainDirective(
        section_id="pol_reg_01",
        section_title="监管合规深度分析",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 合规 要求 标准 门槛 许可", "搜索合规要求"),
            SearchDirective("{query} 处罚 案例 违规 执行", "搜索处罚案例"),
        ],
        analysis_logic=[
            "梳理合规要求清单 — 企业须满足的具体条件",
            "分析准入门槛变化 — 新政策提高了还是降低了门槛",
            "评估违规成本 — 罚款/吊销/刑事责任",
            "搜索典型处罚案例 — 评估执法力度",
        ],
        verification_rules=[
            "合规要求须引用政策原文",
        ],
        pitfall_warnings=[
            "勿将监管意图等同于监管执行力度",
        ],
        output_template=(
            "### 合规要求\n"
            "| 要求 | 原文出处 | 执行力度 |"
        ),
    ),
]

POLICY_INCENTIVE_CHAINS = [
    ThinkingChainDirective(
        section_id="pol_inc_01",
        section_title="激励补贴详细评估",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 补贴 优惠 扶持 减免 标准", "搜索补贴详情"),
            SearchDirective("{query} 申请 条件 流程 期限", "了解申请流程"),
        ],
        analysis_logic=[
            "量化补贴规模 — 具体金额/比例/期限",
            "评估申请门槛 — 谁能享受、需要什么条件",
            "分析可持续性 — 补贴是临时还是长期政策",
            "对比不同地区差异 — 地方加码/缩水情况",
        ],
        verification_rules=[
            "补贴数据须标注政策来源",
        ],
        pitfall_warnings=[
            "勿将补贴政策等同于实际到手补贴",
        ],
        output_template=(
            "### 补贴详情\n"
            "| 类型 | 金额 | 期限 | 申请条件 |"
        ),
    ),
]

POLICY_REFORM_CHAINS = [
    ThinkingChainDirective(
        section_id="pol_ref_01",
        section_title="改革进程与阻力",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 改革 进程 进展 时间表", "追踪改革进度"),
            SearchDirective("{query} 阻力 困难 争议 反对", "分析改革阻力"),
        ],
        analysis_logic=[
            "梳理改革时间线 — 从方案到试点的关键节点",
            "分析改革阻力 — 既得利益方/制度惯性/技术障碍",
            "评估改革成功概率 — 参考历史类似改革案例",
            "预测影响时间表 — 短期/中期/长期各阶段",
        ],
        verification_rules=[
            "改革进度须有官方信息源",
        ],
        pitfall_warnings=[
            "勿将改革方案等同于改革成果",
        ],
        output_template=(
            "### 改革进程\n"
            "| 阶段 | 时间 | 状态 | 阻力 |"
        ),
    ),
]


# === Policy Pre-Search Strategy ===

POLICY_PRE_SEARCH_STRATEGY = PreSearchStrategy(
    mandatory_angle_queries=[
        "{query} 政策原文 公告 {current_year}",
        "{query} 影响 分析 解读 专家",
    ],
    source_search_templates=[
        SourceSearchTemplate(
            name="政策原文",
            query_template="site:gov.cn OR site:www.gov.cn {query} 政策 文件",
            priority="highest",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="权威解读",
            query_template="site:xinhuanet.com OR site:people.com.cn {query} 政策解读",
            priority="high",
            max_results=3,
        ),
    ],
    recency_preference="y",
)


# === Policy Critic Template ===

POLICY_CRITIC_TEMPLATE = """1. **政策原文准确性**：
   - 是否引用了政策原文？是否标注了文号和日期？
   - 分析是否区分了原文内容 vs 解读推测？
2. **影响分析深度**：
   - 是否只看了直接影响，忽略了间接和二阶效应？
   - 是否遗漏了受损方的反弹力量？
3. **实施可行性**：
   - 是否考虑了政策执行的现实障碍？
   - 是否区分了政策出台 vs 实际落地？"""


# === Policy Output Template ===

POLICY_OUTPUT_TEMPLATE = """政策格式：执行摘要/政策解读/影响路径/利益相关方/展望风险。附来源和文号。"""


# === Policy Domain Config ===

# === Policy Analysis Methodology (Phase 4) ===

POLICY_ANALYSIS_METHODOLOGY = """政策分析的核心是政策意图推导和影响链追踪，不是条文罗列。

1.**政策意图推导**:政策文本→直接目标→深层意图→利益格局→政治逻辑
2.**影响传导链**:政策发布→直接影响对象→间接影响对象→次生效应→长期效应
3.**执行偏差预判**:政策意图vs执行可能性的差距→利益相关方博弈→实际效果偏差
4.**历史类比**:类似政策的历史先例→当时的背景→执行效果→可借鉴的经验
5.**利益相关方分析»:谁受益/谁受损/谁有执行权/谁有否决权→政策可行性判断

分析每个政策发现时追问:政策的真实意图是什么?谁推动的?执行阻力在哪?历史先例说明了什么?"""

policy_config = DomainConfig(
    name="政策/法规",
    keywords=["政策", "法规", "监管", "补贴", "改革", "规定", "文件", "公告", "合规", "处罚"],
    thinking_chains=POLICY_THINKING_CHAINS,
    pre_search_strategy=POLICY_PRE_SEARCH_STRATEGY,
    quality_checks=[],  # Will add domain-specific checks later
    critic_template=POLICY_CRITIC_TEMPLATE,
    output_template=POLICY_OUTPUT_TEMPLATE,
    max_directive_tokens=2000,
    analysis_methodology=POLICY_ANALYSIS_METHODOLOGY,
)