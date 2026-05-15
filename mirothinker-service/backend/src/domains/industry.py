"""
MiroThinker - Industry/Industry Analysis Domain Configuration

Thinking chains for industry/sector analysis:
- Industry structure (supply chain, upstream/downstream)
- Competitive landscape (market concentration, leading players)
- Business cycle and trends (policy catalysts, technology disruption)
- Investment perspective and risks (key variables, risk factors)
"""

from src.domains.base import (
    DomainConfig,
    ThinkingChainDirective,
    SearchDirective,
    SourceSearchTemplate,
    PreSearchStrategy,
)


# === 4 Industry Thinking Chains ===

INDUSTRY_THINKING_CHAINS = [
    ThinkingChainDirective(
        section_id="ind_01_structure",
        section_title="一、产业结构与产业链",
        section_order=1,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 产业链 上下游 核心环节", "梳理产业链结构"),
            SearchDirective("{query} 产值 规模 市场容量 TAM", "了解市场规模"),
            SearchDirective("{query} 利润分配 价值链 溢价环节", "分析利润分配"),
        ],
        analysis_logic=[
            "绘制产业链图谱 — 上游原材料→中游制造→下游应用",
            "识别各环节价值占比 — 哪个环节利润最厚、壁垒最高",
            "评估产业链完整性 — 是否有断链风险或进口依赖",
            "分析产业集聚度 — 地域分布、集群效应",
        ],
        verification_rules=[
            "产业链须覆盖完整上下游",
            "产值数据须标注来源和年份",
        ],
        pitfall_warnings=[
            "勿将产业链简化为线性 — 实际多为网状结构",
            "勿忽略替代产业链 — 技术变革可能颠覆现有格局",
        ],
        output_template=(
            "### 产业链图谱\n"
            "上游 → 中游 → 下游\n\n"
            "### 各环节价值占比\n"
            "| 环节 | 产值占比 | 利润率 | 壁垒 |"
        ),
    ),
    ThinkingChainDirective(
        section_id="ind_02_competition",
        section_title="二、竞争格局与龙头",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 市场集中度 CR3 CR5 龙头", "了解竞争格局"),
            SearchDirective("{query} 龙头公司 市值 份额 对比", "对比主要企业"),
            SearchDirective("{query} 进入壁垒 护城河 成本优势", "评估进入门槛"),
        ],
        analysis_logic=[
            "计算市场集中度(CR3/CR5) — 高集中度=寡头垄断,低=充分竞争",
            "对比龙头企业 — 市值/营收/增速/估值/核心优势",
            "评估进入壁垒 — 规模效应/品牌/技术/渠道/牌照",
            "分析竞争动态 — 新进入者/替代品/行业整合趋势",
        ],
        verification_rules=[
            "市场份额须有具体数据支撑",
            "公司对比须基于同口径数据",
        ],
        pitfall_warnings=[
            "勿将市场份额等同于竞争优势",
            "勿忽略潜在颠覆者(技术/商业模式创新)",
        ],
        output_template=(
            "### 竞争格局\n"
            "- 市场集中度: CR3=XX%, CR5=XX%\n"
            "- 竞争类型: 寡头/垄断竞争/完全竞争\n\n"
            "### 龙头对比\n"
            "| 公司 | 市值 | 份额 | 增速 | 核心优势 |"
        ),
    ),
    ThinkingChainDirective(
        section_id="ind_03_cycle",
        section_title="三、景气周期与趋势",
        section_order=3,
        importance="important",
        search_directives=[
            SearchDirective("{query} 景气度 周期 PMI 产能利用率", "判断周期位置"),
            SearchDirective("{query} 政策 支持 规划 十四五", "搜索政策催化"),
            SearchDirective("{query} 技术趋势 创新 变革 数字化", "了解技术趋势"),
        ],
        analysis_logic=[
            "判断周期位置 — 底部/上升/顶部/下降，基于PMI/产能利用率/库存等指标",
            "评估政策催化 — 产业政策/补贴/准入标准/十四五规划",
            "分析技术变革 — 数字化/AI/新材料/新工艺，评估颠覆潜力",
            "预测景气方向 — 上行/平稳/下行，给出置信度",
        ],
        verification_rules=[
            "周期判断须有定量指标支撑",
            "政策须引用具体文件名称",
        ],
        pitfall_warnings=[
            "勿将短期波动当长期趋势",
            "勿忽略周期性行业的均值回归规律",
        ],
        output_template=(
            "### 景气周期\n"
            "- 当前位置: 上升/顶部/下降/底部\n"
            "- 核心指标: PMI/产能利用率/库存\n\n"
            "### 政策催化\n"
            "| 政策 | 影响方向 | 影响程度 |"
        ),
    ),
    ThinkingChainDirective(
        section_id="ind_04_investment",
        section_title="四、投资视角与风险",
        section_order=4,
        importance="supplementary",
        search_directives=[
            SearchDirective("{query} 投资 机会 风险 估值", "搜索投资视角"),
        ],
        analysis_logic=[
            "提炼2-3个核心投资变量 — 哪些因素决定行业走势",
            "列出主要风险 — 政策风险/技术风险/周期风险/竞争风险",
            "给出投资方向建议 — 但标注确定性等级",
            "说明研究局限性",
        ],
        verification_rules=[
            "风险因素须有具体案例支撑",
        ],
        pitfall_warnings=[
            "勿给出超出分析范围的确定性结论",
        ],
        output_template=(
            "### 关键变量\n"
            "1. [变量名] → 影响方向和程度\n\n"
            "### 风险清单\n"
            "| 风险 | 概率 | 影响 | 缓解 |\n\n"
            "### 结论\n"
            "- 核心结论 + 确定性等级"
        ),
    ),
]


# === Industry Subtype Chains ===

INDUSTRY_MANUFACTURING_CHAINS = [
    ThinkingChainDirective(
        section_id="ind_mfg_01",
        section_title="制造业产能与供应链",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 产能 扩产 产能利用率 产能过剩", "评估产能状况"),
            SearchDirective("{query} 供应链 原材料 成本 进口依赖", "分析供应链"),
        ],
        analysis_logic=[
            "评估产能利用率 — >85%=景气, <70%=过剩",
            "分析扩产周期 — 从规划到投产的时间表",
            "评估供应链风险 — 关键原材料进口依赖度",
            "成本结构分析 — 原材料/人工/能源占比",
        ],
        verification_rules=[
            "产能数据须标注时间范围",
        ],
        pitfall_warnings=[
            "勿忽略产能过剩的周期性",
        ],
        output_template=(
            "### 产能状况\n"
            "| 指标 | 数值 | 行业对比 |\n"
            "| 产能利用率 | | |\n"
            "| 扩产计划 | | |"
        ),
    ),
]

INDUSTRY_SERVICE_CHAINS = [
    ThinkingChainDirective(
        section_id="ind_svc_01",
        section_title="服务业平台与数字化",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 平台 经济 数字化 渗透率", "了解数字化程度"),
            SearchDirective("{query} 用户量 GMV 增速 粘性", "分析平台指标"),
        ],
        analysis_logic=[
            "评估平台规模 — 用户/GMV/增速",
            "分析网络效应 — 用户粘性/转换成本/数据壁垒",
            "评估数字化渗透率 — 传统vs数字渠道占比",
            "分析消费趋势 — 需求变化/消费升级/降级",
        ],
        verification_rules=[
            "平台数据须标注来源和时间",
        ],
        pitfall_warnings=[
            "勿将GMV增长等同于盈利能力",
        ],
        output_template=(
            "### 平台指标\n"
            "| 指标 | 数值 | 增速 |\n"
            "| 用户量 | | |\n"
            "| GMV | | |"
        ),
    ),
]

INDUSTRY_EMERGING_CHAINS = [
    ThinkingChainDirective(
        section_id="ind_emg_01",
        section_title="新兴产业渗透与增长",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 渗透率 TAM 增长空间 新技术", "评估增长空间"),
            SearchDirective("{query} 产业化 进展 落地 试点", "追踪产业化进展"),
        ],
        analysis_logic=[
            "计算TAM渗透率 — 低渗透率=高增长潜力",
            "区分实验室vs产业化 — 技术成熟度(TRL)评估",
            "追踪政策支持 — 新兴产业通常有补贴/扶持",
            "评估0→1突破节点 — 何时从概念走向规模",
        ],
        verification_rules=[
            "渗透率须有行业数据支撑",
        ],
        pitfall_warnings=[
            "勿将早期增长线性外推",
            "勿忽略技术路径不确定性",
        ],
        output_template=(
            "### 渗透与增长\n"
            "| 指标 | 数值 | 预期 |\n"
            "| TAM渗透率 | | |\n"
            "| 技术成熟度 | | |"
        ),
    ),
]


# === Industry Pre-Search Strategy ===

INDUSTRY_PRE_SEARCH_STRATEGY = PreSearchStrategy(
    mandatory_angle_queries=[
        "{query} 产业链 产业结构 最新 {current_year}",
        "{query} 竞争格局 龙头 市场份额",
    ],
    source_search_templates=[
        SourceSearchTemplate(
            name="产业报告",
            query_template="site:miit.gov.cn OR site:stats.gov.cn {query} 产业报告",
            priority="high",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="行业协会",
            query_template="site:miit.gov.cn OR site:cas.org.cn {query} 行业协会 数据",
            priority="medium",
            max_results=3,
        ),
    ],
    recency_preference="y",
)


# === Industry Critic Template ===

INDUSTRY_CRITIC_TEMPLATE = """1. **产业链完整性**：
   - 是否遗漏了关键环节或替代产业链？
   - 上下游分析是否足够深入？
2. **竞争格局**：
   - 是否只看了头部，忽略了新进入者或颠覆者？
   - 市场集中度数据是否来自可靠来源？
3. **周期判断**：
   - 景气周期判断是否有定量指标支撑？
   - 是否考虑了周期性风险？"""


# === Industry Output Template ===

INDUSTRY_OUTPUT_TEMPLATE = """产业格式：执行摘要/产业链/竞争格局/景气周期/投资视角/风险。用表格，附来源。"""


# === Industry Domain Config ===

# === Industry Analysis Methodology (Phase 4) ===

INDUSTRY_ANALYSIS_METHODOLOGY = """产业分析的核心是产业链因果推导和竞争动态，不是行业数据罗列。

1.**产业链传导链**:上游→中游→下游→终端，每个环节的供需变化如何传导
2.**竞争格局推导**:市场集中度→竞争者行为→定价权→利润分配→演进方向
3.**周期定位**:行业当前处于什么周期位置(成长期/成熟期/衰退期/转型期)?依据是什么?
4.**结构性变化识别**:行业变化是周期性波动还是结构性转变?判断依据?
5.**政策影响路径**:政策→直接影响→间接影响→长期影响，逐层推导

分析每个产业发现时追问:这个变化会影响产业链哪个环节?是周期性还是结构性?竞争者如何反应?"""

industry_config = DomainConfig(
    name="产业/行业",
    keywords=["产业", "行业", "产业链", "制造业", "服务业", "新兴产业", "新能源", "AI产业", "行业分析"],
    thinking_chains=INDUSTRY_THINKING_CHAINS,
    pre_search_strategy=INDUSTRY_PRE_SEARCH_STRATEGY,
    quality_checks=[],  # Will add domain-specific checks later
    critic_template=INDUSTRY_CRITIC_TEMPLATE,
    output_template=INDUSTRY_OUTPUT_TEMPLATE,
    max_directive_tokens=2000,
    analysis_methodology=INDUSTRY_ANALYSIS_METHODOLOGY,
)