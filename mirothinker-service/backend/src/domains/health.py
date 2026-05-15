"""
MiroThinker - Health Domain Configuration

7 Thinking Chain Directives for health/medical analysis,
covering evidence levels, safety, alternatives, and research quality.
"""

import re
from src.domains.base import (
    DomainConfig,
    ThinkingChainDirective,
    SearchDirective,
    SourceSearchTemplate,
    PreSearchStrategy,
)


# === 7 Health Thinking Chains ===

HEALTH_THINKING_CHAINS = [
    ThinkingChainDirective(
        section_id="health_01_mechanism",
        section_title="一、背景与机制",
        section_order=1,
        importance="supplementary",
        search_directives=[
            SearchDirective("{query} mechanism of action 作用机制", "了解生物学机制"),
            SearchDirective("{query} background overview 背景 概述", "获取背景信息"),
        ],
        analysis_logic=[
            "解释生物学/药理学机制 — 用通俗语言",
            "区分与类似治疗/方法的关键差异",
            "标注机制理解的不确定性 — 已验证 vs 假说",
        ],
        verification_rules=[
            "机制描述须引用学术文献",
            "动物实验结果不能等同于人体效果",
        ],
        pitfall_warnings=[
            "勿将体外(in vitro)结果等同于体内(in vivo)效果",
            "勿忽略机制复杂性 — 大多数治疗不是单一靶点",
        ],
        output_template=(
            "### 生物学/药理机制\n"
            "- 通俗解释 + 学术引用\n\n"
            "### 与类似方法的关键差异\n"
            "- 核心区别点"
        ),
    ),
    ThinkingChainDirective(
        section_id="health_02_evidence",
        section_title="二、证据等级评估",
        section_order=2,
        importance="critical",
        search_directives=[
            SearchDirective("{query} systematic review meta-analysis 系统综述 荟萃分析", "获取最高等级证据"),
            SearchDirective("{query} clinical trial phase RCT 临床试验", "获取临床试验数据"),
            SearchDirective("{query} guideline recommendation 指南 推荐 {current_year}", "获取权威指南"),
        ],
        analysis_logic=[
            "分类证据等级：I(荟萃分析) / II(RCT) / III(队列研究) / IV(病例系列) / V(专家意见)",
            "评估样本量 — N<30为初步研究，N<100须谨慎解读",
            "检查研究设计 — 双盲、随机、对照 vs 观察性",
            "区分绝对效果vs相对效果 — 相对风险降低可能被夸大",
        ],
        verification_rules=[
            "每个疗效声明须标注证据等级和样本量",
            "效果量(Effect Size)须报告，不能只报告p值",
            "冲突研究必须呈现，并分析可能的原因",
        ],
        pitfall_warnings=[
            "勿将初步研究当作定论 — 须标注证据等级",
            "勿混淆相关性与因果性 — 观察性研究≠因果推断",
            "勿忽略发表偏倚 — 阴性结果可能未被发表",
        ],
        output_template=(
            "### 证据等级汇总\n"
            "| 证据类型 | 等级 | 样本量 | 关键结论 |\n"
            "|---------|------|-------|---------|\n"
            "| 荟萃分析 | I | N= | |\n"
            "| RCT | II | N= | |\n\n"
            "### 效果量评估\n"
            "- 绝对风险降低(ARR) / 相对风险降低(RRR) / NNT"
        ),
    ),
    ThinkingChainDirective(
        section_id="health_03_safety",
        section_title="三、安全性与副作用",
        section_order=3,
        importance="critical",
        search_directives=[
            SearchDirective("{query} side effects adverse events 副作用 不良反应", "获取安全性数据"),
            SearchDirective("{query} contraindications warnings 禁忌症 警告", "获取禁忌症信息"),
            SearchDirective("{query} drug interactions 药物相互作用", "了解药物交互风险"),
        ],
        analysis_logic=[
            "区分常见副作用(>10%)和严重副作用(<1%但危及生命)",
            "列出禁忌症 — 哪些人群/情况绝对不能用",
            "标注药物相互作用 — 特别是常见药物的联用风险",
            "比较副作用与替代方案 — 利弊权衡",
        ],
        verification_rules=[
            "副作用须标注发生率（不能只说'可能引起'）",
            "严重副作用必须明确标注",
        ],
        pitfall_warnings=[
            "勿忽略罕见但严重的副作用",
            "勿混淆副作用和疾病自然病程",
            "勿将短期安全性数据外推至长期",
        ],
        output_template=(
            "### 常见副作用(>10%)\n"
            "| 副作用 | 发生率 | 严重程度 |\n"
            "|-------|-------|---------|\n\n"
            "### 严重副作用(<1%)\n"
            "- [列出并标注紧急处理建议]\n\n"
            "### 禁忌症\n"
            "- 绝对禁忌 / 相对禁忌\n\n"
            "### 药物相互作用\n"
            "- 主要联用风险"
        ),
    ),
    ThinkingChainDirective(
        section_id="health_04_alternatives",
        section_title="四、替代治疗方案",
        section_order=4,
        importance="important",
        search_directives=[
            SearchDirective("{query} vs alternatives comparison 替代治疗 对比", "获取替代方案数据"),
            SearchDirective("{query} treatment options 治疗选择 方案", "了解可选方案"),
        ],
        analysis_logic=[
            "建立替代方案对比表 — 疗效、安全性、成本、便利性",
            "标注各方案的适用人群 — 不同人群可能首选不同方案",
            "评估个体化因素 — 年龄、合并症、患者偏好",
        ],
        verification_rules=[
            "疗效对比须基于同类型研究（RCT vs RCT）",
            "不能只比较疗效，须同时比较安全性和成本",
        ],
        pitfall_warnings=[
            "勿只推荐一种方案 — 须呈现替代选择",
            "勿忽略患者个体化需求",
        ],
        output_template=(
            "### 替代方案对比\n"
            "| 维度 | [本方案] | 替代A | 替代B |\n"
            "|------|---------|-------|-------|\n"
            "| 疗效 | | | |\n"
            "| 安全性 | | | |\n"
            "| 成本 | | | |\n"
            "| 便利性 | | | |"
        ),
    ),
    ThinkingChainDirective(
        section_id="health_05_research_quality",
        section_title="五、研究质量评估",
        section_order=5,
        importance="important",
        search_directives=[
            SearchDirective("{query} study funding source conflict interest 资金 利益冲突", "检查研究偏见"),
        ],
        analysis_logic=[
            "评估资金偏见 — 产业资助的研究结果需额外审视",
            "检查利益冲突 — 研究者是否与药企有关联",
            "样本量评估 — 是否有足够的统计效力",
            "随访时间 — 短期研究可能遗漏长期效应",
        ],
        verification_rules=[
            "产业资助研究须明确标注",
            "样本量不足以得出结论的须标注",
        ],
        pitfall_warnings=[
            "勿忽略资金来源对研究结论的潜在影响",
            "勿将荟萃分析等同于高质量证据 — 须检查纳入研究质量",
        ],
        output_template=(
            "### 研究质量评估\n"
            "| 评估维度 | 状态 | 备注 |\n"
            "|---------|------|------|\n"
            "| 资金来源 | | |\n"
            "| 利益冲突 | | |\n"
            "| 样本量充分性 | | |\n"
            "| 随访时间 | | |"
        ),
    ),
    ThinkingChainDirective(
        section_id="health_06_population",
        section_title="六、适用人群与限制",
        section_order=6,
        importance="supplementary",
        search_directives=[
            SearchDirective("{query} population indications 适用人群 适应症", "了解适用范围"),
            SearchDirective("{query} off-label limitations 超适应症 局限性", "了解使用限制"),
        ],
        analysis_logic=[
            "明确获批适应症 vs 超适应症使用",
            "特殊人群注意 — 孕妇、儿童、老年人、肝肾功能不全",
            "地域差异 — 不同国家/地区的获批情况可能不同",
        ],
        verification_rules=[
            "适应症声明须引用官方批准文件",
        ],
        pitfall_warnings=[
            "勿混淆获批适应症和超适应症使用",
            "勿忽略特殊人群的安全性数据缺失",
        ],
        output_template=(
            "### 获批适应症\n"
            "- [列出并标注批准机构/日期]\n\n"
            "### 特殊人群注意事项\n"
            "- 孕妇/儿童/老年人/肝肾功能不全\n\n"
            "### 超适应症使用\n"
            "- 须标注证据等级和风险"
        ),
    ),
    ThinkingChainDirective(
        section_id="health_07_conclusion",
        section_title="七、结论与建议",
        section_order=7,
        importance="supplementary",
        search_directives=[],
        analysis_logic=[
            "平衡证据强度与实用建议 — 证据不足时须明确标注",
            "标注不确定性 — 已确认/有前景但待验证/有争议",
            "给出实用建议 — 但须声明不构成医疗建议",
        ],
        verification_rules=[
            "建议须与证据等级一致 — 不能基于低等级证据给强推荐",
        ],
        pitfall_warnings=[
            "勿给出与证据等级不符的强烈建议",
            "勿忽略免责声明 — AI分析不构成医疗建议",
        ],
        output_template=(
            "### 证据强度总结\n"
            "| 结论 | 证据等级 | 确定性 |\n"
            "|------|---------|-------|\n\n"
            "### 实用建议\n"
            "- [须声明：不构成医疗建议，请咨询专业医生]\n\n"
            "### 研究局限性\n"
            "- 数据限制 + 评估范围"
        ),
    ),
]


# === Health Pre-Search Strategy ===

HEALTH_PRE_SEARCH_STRATEGY = PreSearchStrategy(
    mandatory_angle_queries=[
        "{query} 最新研究 {current_year}",
        "{query} 副作用 风险 安全性",
        "{query} 替代治疗 对比 选择",
        "{query} 禁忌症 适应症 注意事项",
    ],
    source_search_templates=[
        SourceSearchTemplate(
            name="医学文献",
            query_template="site:pubmed.ncbi.nlm.nih.gov OR site:ncbi.nlm.nih.gov {query}",
            priority="highest",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="权威指南",
            query_template="site:who.int OR site:nih.gov OR site:cochrane.org {query}",
            priority="highest",
            max_results=3,
        ),
        SourceSearchTemplate(
            name="学术信源",
            query_template="site:scholar.google.com OR site:arxiv.org OR site:nejm.org {query}",
            priority="high",
            max_results=3,
        ),
    ],
    recency_preference="y",
)


# === Health Quality Checks ===

def check_health_evidence_level(result: str, metadata: dict) -> dict:
    """Check if evidence levels are classified."""
    has_evidence = bool(re.search(
        r'证据等级|evidence level|RCT|meta.?analysis|荟萃分析|系统综述|'
        r'cohort|队列研究|case.?control|病例对照|观察性研究',
        result, re.IGNORECASE
    ))
    if has_evidence:
        return {"score": 1.0, "issues": []}
    return {"score": 0.2, "issues": ["CRITICAL: 医学分析缺少证据等级分类（I-V级）"]}


def check_health_sample_size(result: str, metadata: dict) -> dict:
    """Check if study sample sizes are reported."""
    has_sample = bool(re.search(r'N=\d+|样本量|sample size|参与者|受试者|\d+名患者|\d+例患者', result, re.IGNORECASE))
    if has_sample:
        return {"score": 1.0, "issues": []}
    return {"score": 0.4, "issues": ["医学分析建议报告研究样本量"]}


def check_health_side_effects(result: str, metadata: dict) -> dict:
    """Check if side effects are covered."""
    has_effects = bool(re.search(
        r'副作用|不良反应|adverse|side effect|安全性|safety',
        result, re.IGNORECASE
    ))
    if has_effects:
        return {"score": 1.0, "issues": []}
    return {"score": 0.1, "issues": ["CRITICAL: 医学分析缺少副作用/安全性评估"]}


def check_health_contraindications(result: str, metadata: dict) -> dict:
    """Check if contraindications are mentioned."""
    has_contra = bool(re.search(
        r'禁忌|contraindication|注意事项|warning|不宜',
        result, re.IGNORECASE
    ))
    if has_contra:
        return {"score": 1.0, "issues": []}
    return {"score": 0.3, "issues": ["医学分析建议包含禁忌症信息"]}


def check_health_causation_vs_correlation(result: str, metadata: dict) -> dict:
    """Check if correlation vs causation is distinguished."""
    has_distinction = bool(re.search(
        r'相关性|因果|correlation|causation|关联|不能确定因果|'
        r'confounding|混杂因素|观察性研究.*?因果',
        result, re.IGNORECASE
    ))
    if has_distinction:
        return {"score": 1.0, "issues": []}
    return {"score": 0.5, "issues": ["医学分析须区分相关性与因果性"]}


HEALTH_QUALITY_CHECKS = [
    check_health_evidence_level,
    check_health_sample_size,
    check_health_side_effects,
    check_health_contraindications,
    check_health_causation_vs_correlation,
]


# === Health Critic Template ===

HEALTH_CRITIC_TEMPLATE = """1. **视角完整性**：
   - 是否区分了证据等级（I-V级）？
   - 是否报告了研究的样本量和设计类型？
   - 是否覆盖了副作用和禁忌症？
   - 是否标注了研究资金来源（产业资助需额外审视）？
   - 是否区分了相关性与因果性？
   - 是否包含免责声明（AI分析不构成医疗建议）？"""


# === Health Output Template ===

HEALTH_OUTPUT_TEMPLATE = """健康格式：机制/证据/安全性/替代方案/结论。附免责声明：不构成医疗建议。附来源。"""


# === Health Domain Config ===

# === Health Analysis Methodology (Phase 4) ===

HEALTH_ANALYSIS_METHODOLOGY = """医疗健康分析的核心是证据链条和因果推断，不是症状罗列。

1.**证据等级评估**:系统综述/RCT→队列研究→病例对照→专家意见，判断证据强度
2.**因果推断链**:暴露因素→生物学机制→临床证据→流行病学数据→因果关系判断
3.**获益-风险推导**:治疗效果→副作用谱→适用人群→禁忌症→净获益评估
4.**争议识别**:不同指南/研究结论的差异→原因分析(人群/方法/利益冲突)→当前共识
5.**预防→诊断→治疗→预后链**:完整疾病管理路径的每个环节是否有证据支撑

分析每个健康发现时追问:证据等级是什么?因果关系还是相关关系?是否有充分对照?结论适用范围?"""

health_config = DomainConfig(
    name="医疗/健康",
    keywords=[
        "健康", "医疗", "疾病", "治疗", "药物", "疫苗", "临床", "副作用",
        "手术", "诊断", "症状", "康复", "预防", "营养", "心理", "中医",
        "health", "medical", "disease", "treatment", "medicine", "drug",
        "vaccine", "clinical", "therapy", "diagnosis", "patient", "hospital",
        "疗效", "安全性", "禁忌症", "适应症", "不良反应",
    ],
    thinking_chains=HEALTH_THINKING_CHAINS,
    pre_search_strategy=HEALTH_PRE_SEARCH_STRATEGY,
    quality_checks=HEALTH_QUALITY_CHECKS,
    critic_template=HEALTH_CRITIC_TEMPLATE,
    output_template=HEALTH_OUTPUT_TEMPLATE,
    max_directive_tokens=2500,
    analysis_methodology=HEALTH_ANALYSIS_METHODOLOGY,
)
