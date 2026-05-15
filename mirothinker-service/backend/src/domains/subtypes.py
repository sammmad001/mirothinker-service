"""
MiroThinker - Entity Subtype Definitions

Each domain has multiple entity subtypes that require different analysis focuses.
The subtype is now determined by LLM classification (qwen-flash), not by keyword matching.
This module only defines the supplement thinking chains for each subtype.

For example, "汇绿生态" (concept play) and "贵州茅台" (blue chip) are both
in the finance domain, but need very different analysis approaches.
"""

from src.domains.base import ThinkingChainDirective, SearchDirective

# Import new domain subtype chains
from src.domains.industry import (
    INDUSTRY_MANUFACTURING_CHAINS,
    INDUSTRY_SERVICE_CHAINS,
    INDUSTRY_EMERGING_CHAINS,
)
from src.domains.policy import (
    POLICY_REGULATION_CHAINS,
    POLICY_INCENTIVE_CHAINS,
    POLICY_REFORM_CHAINS,
)
from src.domains.macro import (
    MACRO_MONETARY_CHAINS,
    MACRO_FISCAL_CHAINS,
    MACRO_GLOBAL_CHAINS,
)


# ============================================================
# FINANCE SUBTYPES
# ============================================================

FINANCE_CONCEPT_PLAY_CHAINS = [
    ThinkingChainDirective(
        section_id="fin_concept_01",
        section_title="概念炒作与资金分析",
        section_order=2,  # Insert after 投资摘要, before 公司概况
        importance="critical",
        search_directives=[
            SearchDirective("{query} 概念股 炒作 逻辑 龙头", "识别概念炒作逻辑"),
            SearchDirective("{query} 游资 机构 资金流向 龙虎榜", "分析资金动向"),
            SearchDirective("{query} 涨停 连板 换手率 成交量", "评估市场热度"),
            SearchDirective("{query} 概念 持续性 退潮 风险", "评估概念持久性"),
        ],
        analysis_logic=[
            "识别当前炒作的核心概念 — 是政策驱动/事件驱动/题材驱动",
            "分析资金结构 — 游资主导 vs 机构参与（机构参与度越高，持续性越强）",
            "评估概念阶段 — 起步期(可关注)/加速期(高风险)/退潮期(必须警示)",
            "计算换手率和成交量异常 — 换手率>20%需警惕短期见顶",
            "对比历史类似概念 — 持续了多久？最终结局如何？",
        ],
        verification_rules=[
            "概念声明须有具体事件或政策支撑",
            "资金流向数据须来自龙虎榜或权威数据",
        ],
        pitfall_warnings=[
            "勿将概念炒作当基本面改善 — 概念退潮后股价大概率回归",
            "勿忽略大股东减持 — 概念炒作期间减持是强烈看空信号",
            "勿追涨杀跌建议 — 须明确标注高风险",
        ],
        output_template=(
            "### 概念分析\n"
            "| 维度 | 内容 |\n"
            "|------|------|\n"
            "| 核心概念 | [政策/事件/题材]驱动 |\n"
            "| 炒作阶段 | 起步/加速/退潮 |\n"
            "| 资金结构 | 游资/机构比例 |\n"
            "| 持续性评估 | 高/中/低 + 理由 |\n\n"
            "### 历史类似概念对比\n"
            "| 概念 | 持续时间 | 最终结局 |"
        ),
    ),
    ThinkingChainDirective(
        section_id="fin_concept_02",
        section_title="转型/变更深度追踪",
        section_order=3,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 转型 算力 AI 新能源 进展", "追踪转型实际进展"),
            SearchDirective("{query} 公告 变更 经营范围 投资", "核实官方公告"),
            SearchDirective("{query} 转型 营收占比 实际贡献", "评估转型对业绩的实际影响"),
        ],
        analysis_logic=[
            "区分'宣布转型' vs '实际产生收入' — 很多公司只宣布不落地",
            "计算新业务营收占比 — 如果<5%，转型仍是概念阶段",
            "检查转型投资规模 — 投资金额vs公司市值，占比过低可能只是做样子",
            "追踪转型公告时间线 — 从公告到落地需要多久",
        ],
        verification_rules=[
            "转型声明须有官方公告支撑（巨潮资讯）",
            "营收占比数据须来自年报/季报",
        ],
        pitfall_warnings=[
            "勿将'签署框架协议'等同于'业务落地'",
            "勿忽略转型失败的风险 — 大多数跨界转型以失败告终",
        ],
        output_template=(
            "### 转型进展追踪\n"
            "| 时间 | 事件 | 性质 | 实际影响 |\n"
            "|------|------|------|---------|\n"
            "| | 公告/签约/投产 | 概念/落地 | 高/中/低 |\n\n"
            "### 新业务实际贡献\n"
            "- 新业务营收占比: XX%\n"
            "- 评估: 概念阶段 / 落地阶段 / 贡献阶段"
        ),
    ),
]

FINANCE_BLUE_CHIP_CHAINS = [
    ThinkingChainDirective(
        section_id="fin_bluechip_01",
        section_title="护城河与长期竞争力",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 护城河 品牌 壁垒 竞争优势", "评估护城河深度"),
            SearchDirective("{query} 市场份额 行业地位 龙头", "确认行业地位"),
            SearchDirective("{query} 分红 股息率 回购 股东回报", "评估股东回报"),
        ],
        analysis_logic=[
            "识别护城河类型并评估强度 — 品牌壁垒/网络效应/成本优势/转换成本",
            "评估护城河是否在被侵蚀 — 新进入者/替代品/技术变化",
            "计算股息率和分红连续性 — 连续5年以上分红是蓝筹标志",
            "评估管理层资本配置能力 — 回购/分红/再投资的平衡",
        ],
        verification_rules=[
            "护城河声明须有市场份额或定价权数据支撑",
            "股息率须基于实际分红数据计算",
        ],
        pitfall_warnings=[
            "勿将'知名品牌'等同于'不可替代' — 消费者偏好可能改变",
            "勿忽略蓝筹股的周期性 — 即使茅台也有增速放缓期",
        ],
        output_template=(
            "### 护城河评估\n"
            "| 护城河类型 | 强度 | 侵蚀风险 |\n"
            "|----------|------|---------|\n\n"
            "### 股东回报\n"
            "| 年份 | 股息率 | 分红率 | 回购金额 |"
        ),
    ),
]

FINANCE_TURNAROUND_CHAINS = [
    ThinkingChainDirective(
        section_id="fin_turnaround_01",
        section_title="困境与重整分析",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} ST 退市 风险 警示", "评估退市风险"),
            SearchDirective("{query} 破产重整 债务重组 引入战投", "追踪重整进展"),
            SearchDirective("{query} 诉讼 冻结 执行 处罚", "检查法律风险"),
        ],
        analysis_logic=[
            "评估退市风险等级 — 是否触及财务类/交易类/规范类退市标准",
            "分析债务结构 — 短期借款vs现金储备、到期债务时间表",
            "评估重整方案可行性 — 战投实力、方案执行进度",
            "计算困境反转的概率 — 基于5-10个类似案例的历史统计",
        ],
        verification_rules=[
            "退市风险须对照交易所退市规则逐条评估",
            "债务数据须来自最新财报",
        ],
        pitfall_warnings=[
            "勿将'重整方案通过'等同于'困境反转成功'",
            "勿忽略重整失败后退市的风险 — 须明确标注",
        ],
        output_template=(
            "### 退市风险评估\n"
            "| 退市标准 | 当前状态 | 风险等级 |\n"
            "|---------|---------|---------|\n\n"
            "### 重整进展\n"
            "- 债务规模 / 已解决比例 / 关键节点时间表"
        ),
    ),
]

FINANCE_HIGH_GROWTH_CHAINS = [
    ThinkingChainDirective(
        section_id="fin_growth_01",
        section_title="增长引擎与可扩展性",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 增速 增长率 TAM 渗透率", "评估增长空间"),
            SearchDirective("{query} 产能 扩产 产能利用率", "评估产能扩张"),
            SearchDirective("{query} 客户 订单 在手订单 积压", "评估需求景气度"),
        ],
        analysis_logic=[
            "计算TAM渗透率 — 低渗透率=高增长空间",
            "区分内生增长vs外延并购 — 并购驱动的增长不可持续",
            "评估产能扩张节奏 — 过快扩产可能引发产能过剩",
            "检查增长质量 — 营收增长是否带来利润增长（增收又增利 vs 增收不增利）",
        ],
        verification_rules=[
            "增速数据须标注时间范围（CAGR 3年/5年）",
            "渗透率须有行业数据支撑",
        ],
        pitfall_warnings=[
            "勿将高增速线性外推 — 增速必然随规模增大而放缓",
            "勿忽略增收不增利 — 毛利率下降的高增长是危险信号",
        ],
        output_template=(
            "### 增长分析\n"
            "| 指标 | 数值 | 行业对比 |\n"
            "|------|------|---------|\n"
            "| 营收CAGR(3年) | | |\n"
            "| 净利润CAGR(3年) | | |\n"
            "| TAM渗透率 | | |"
        ),
    ),
]

# Sector/Theme research
FINANCE_SECTOR_THEME_CHAINS = [
    ThinkingChainDirective(
        section_id="fin_sector_01",
        section_title="板块全景与产业链",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 产业链 上下游 核心公司", "梳理产业链"),
            SearchDirective("{query} 龙头公司 市值 排名 对比", "对比板块龙头"),
            SearchDirective("{query} 政策 景气度 周期 机构观点", "评估板块景气"),
        ],
        analysis_logic=[
            "绘制产业链图谱 — 上游/中游/下游/核心环节",
            "识别各环节龙头 — 市值、增速、估值对比",
            "评估板块景气周期位置 — 底部/上升/顶部/下降",
            "分析政策催化 — 当前和预期的政策支持",
        ],
        verification_rules=[
            "产业链须覆盖完整上下游",
            "公司对比须基于相同口径数据",
        ],
        pitfall_warnings=[
            "勿将板块景气等同于个股机会",
            "勿忽略产业链各环节的利润分配差异",
        ],
        output_template=(
            "### 产业链图谱\n"
            "上游 → 中游 → 下游\n\n"
            "### 板块龙头对比\n"
            "| 公司 | 市值 | PE | 营收增速 | 核心优势 |"
        ),
    ),
]

# Macro/Strategy research
FINANCE_MACRO_STRATEGY_CHAINS = [
    ThinkingChainDirective(
        section_id="fin_macro_01",
        section_title="宏观环境与政策分析",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 宏观 经济 政策 央行", "了解宏观背景"),
            SearchDirective("{query} 利率 流动性 M2 社融", "分析流动性"),
        ],
        analysis_logic=[
            "分析当前宏观周期位置 — 复苏/扩张/滞胀/衰退",
            "评估货币政策方向 — 宽松/中性/紧缩",
            "判断大类资产配置方向 — 股/债/商品/现金",
        ],
        verification_rules=[
            "宏观数据须标注来源和时效性",
        ],
        pitfall_warnings=[
            "勿将单一指标当宏观趋势",
        ],
        output_template=(
            "### 宏观周期\n"
            "- 当前阶段: / 核心驱动: / 预期方向:"
        ),
    ),
]


# ============================================================
# TECH SUBTYPES
# ============================================================

TECH_COMPARISON_CHAINS = [
    ThinkingChainDirective(
        section_id="tech_compare_01",
        section_title="深度对比分析框架",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} pros cons advantages disadvantages 优缺点", "获取优缺点对比"),
            SearchDirective("{query} use case when to choose 适用场景", "了解适用场景"),
            SearchDirective("{query} migration cost switching cost 迁移成本", "评估迁移成本"),
        ],
        analysis_logic=[
            "建立决策树 — 什么场景选A，什么场景选B",
            "量化迁移成本 — 学习曲线、代码改动量、数据迁移",
            "评估社区趋势 — 哪个方向在获得更多采用",
        ],
        verification_rules=[
            "对比须基于同一场景，不能A的最佳场景vs B的劣势场景",
        ],
        pitfall_warnings=[
            "勿用主观偏好代替客观对比",
        ],
        output_template=(
            "### 决策矩阵\n"
            "| 场景 | 推荐 | 理由 |"
        ),
    ),
]

TECH_TUTORIAL_CHAINS = [
    ThinkingChainDirective(
        section_id="tech_tutorial_01",
        section_title="实践指南与最佳实践",
        section_order=2,
        importance="important",
        search_directives=[
            SearchDirective("{query} tutorial getting started 最佳实践 实践指南", "获取实践指南"),
            SearchDirective("{query} common mistakes pitfalls 常见错误 踩坑", "了解常见问题"),
        ],
        analysis_logic=[
            "组织从入门到进阶的学习路径",
            "列出最常见的新手错误及解决方案",
        ],
        verification_rules=[
            "代码示例须可运行 — 标注版本号",
        ],
        pitfall_warnings=[
            "勿忽略版本兼容性",
        ],
        output_template=(
            "### 快速上手\n"
            "- 环境要求 + 安装步骤 + Hello World\n\n"
            "### 常见坑点\n"
            "1. ..."
        ),
    ),
]


# ============================================================
# HEALTH SUBTYPES
# ============================================================

HEALTH_TREATMENT_CHAINS = [
    ThinkingChainDirective(
        section_id="health_treatment_01",
        section_title="治疗方案综合评估",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} 临床效果 有效率 治愈率", "获取疗效数据"),
            SearchDirective("{query} 费用 医保 价格 成本", "了解治疗成本"),
            SearchDirective("{query} 指南 推荐 一线二线", "获取权威指南推荐"),
        ],
        analysis_logic=[
            "区分一线/二线/三线治疗 — 指南推荐等级",
            "评估性价比 — 疗效/费用/便利性综合评分",
            "分析医保覆盖 — 是否纳入医保目录",
        ],
        verification_rules=[
            "疗效数据须标注研究类型和样本量",
        ],
        pitfall_warnings=[
            "勿将早期临床试验结果等同于成熟治疗方案",
        ],
        output_template=(
            "### 治疗方案评估\n"
            "| 维度 | 评分 | 说明 |\n"
            "|------|------|------|\n"
            "| 疗效 | | |\n"
            "| 安全性 | | |\n"
            "| 成本 | | |"
        ),
    ),
]

HEALTH_PREVENTION_CHAINS = [
    ThinkingChainDirective(
        section_id="health_prevention_01",
        section_title="预防与保健建议",
        section_order=2,
        importance="important",
        search_directives=[
            SearchDirective("{query} 预防 保健 生活方式 风险因素", "获取预防建议"),
        ],
        analysis_logic=[
            "区分可修改风险因素 vs 不可修改风险因素",
            "评估预防措施的证据等级",
        ],
        verification_rules=[
            "预防建议须标注证据等级",
        ],
        pitfall_warnings=[
            "勿将观察性研究结果当因果证据",
        ],
        output_template=(
            "### 风险因素\n"
            "| 因素 | 可修改 | 证据等级 |"
        ),
    ),
]


# ============================================================
# SUBTYPE REGISTRY
# ============================================================

# Maps (domain, subtype_key) → list of supplement thinking chains
SUBTYPE_CHAINS = {
    ("finance", "concept_play"): FINANCE_CONCEPT_PLAY_CHAINS,
    ("finance", "blue_chip"): FINANCE_BLUE_CHIP_CHAINS,
    ("finance", "turnaround"): FINANCE_TURNAROUND_CHAINS,
    ("finance", "high_growth"): FINANCE_HIGH_GROWTH_CHAINS,
    ("finance", "sector_theme"): FINANCE_SECTOR_THEME_CHAINS,
    ("finance", "macro_strategy"): FINANCE_MACRO_STRATEGY_CHAINS,
    ("tech", "comparison"): TECH_COMPARISON_CHAINS,
    ("tech", "tutorial"): TECH_TUTORIAL_CHAINS,
    ("health", "treatment"): HEALTH_TREATMENT_CHAINS,
    ("health", "prevention"): HEALTH_PREVENTION_CHAINS,
    # Industry subtypes
    ("industry", "manufacturing"): INDUSTRY_MANUFACTURING_CHAINS,
    ("industry", "service"): INDUSTRY_SERVICE_CHAINS,
    ("industry", "emerging"): INDUSTRY_EMERGING_CHAINS,
    # Policy subtypes
    ("policy", "regulation"): POLICY_REGULATION_CHAINS,
    ("policy", "incentive"): POLICY_INCENTIVE_CHAINS,
    ("policy", "reform"): POLICY_REFORM_CHAINS,
    # Macro subtypes
    ("macro", "monetary"): MACRO_MONETARY_CHAINS,
    ("macro", "fiscal"): MACRO_FISCAL_CHAINS,
    ("macro", "global"): MACRO_GLOBAL_CHAINS,
}
