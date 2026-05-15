"""
MiroThinker - Dynamic Classification Prompt Builder

Generates classification prompts dynamically from DOMAIN_REGISTRY
and SUBTYPE_CHAINS, eliminating hardcoded domain/subtype lists.
"""

from src.domains.registry import DOMAIN_REGISTRY
from src.domains.subtypes import SUBTYPE_CHAINS


def build_classify_prompt(query: str) -> str:
    """Build classification prompt dynamically from domain registry.

    Instead of hardcoded domain/subtype lists, this function:
    1. Iterates DOMAIN_REGISTRY to generate domain options
    2. Iterates SUBTYPE_CHAINS to generate subtype options per domain
    3. Assembles the complete prompt with dynamic content

    This means adding a new domain only requires registering it in
    DOMAIN_REGISTRY — no prompt editing needed.
    """
    # 1. Build domain options from registry
    domain_lines = []
    for name, config in DOMAIN_REGISTRY.items():
        domain_lines.append(f"- {name}: {config.name}")

    # 2. Build subtype options per domain from SUBTYPE_CHAINS
    domain_subtypes = {}
    subtype_descriptions = _get_subtype_descriptions()
    for (domain, subtype_key) in SUBTYPE_CHAINS.keys():
        if domain not in domain_subtypes:
            domain_subtypes[domain] = []
        desc = subtype_descriptions.get(subtype_key, subtype_key)
        domain_subtypes[domain].append(f"{subtype_key}: {desc}")

    # 3. Assemble prompt
    domain_section = "\n".join(domain_lines)

    subtype_sections = []
    for domain, subtypes in domain_subtypes.items():
        subtype_lines = "\n".join(f"  - {s}" for s in subtypes)
        subtype_sections.append(f"{domain}子类型（仅当领域为{domain}时选择）：\n{subtype_lines}")

    subtype_text = "\n\n".join(subtype_sections)

    prompt = f"""你是一个查询路由分类器。请对用户查询进行三级分类：

## 1. 复杂度分级 (Tier)
- TIER_1: 简单事实性问题，可直接回答
- TIER_2: 需要一些研究，但相对直接
- TIER_3: 深度研究，多源分析，复杂推理

## 2. 领域分级 (Domain)
{domain_section}

## 3. 子类型
{subtype_text}

用户查询：{query}

请严格按以下JSON格式返回，不要添加任何其他内容：
{{"tier": "TIER_1/2/3", "domain": "领域key", "subtype": "子类型key或null"}}"""

    return prompt


# Subtype descriptions for prompt generation
_SUBTYPE_DESCRIPTIONS = {
    # Finance subtypes
    "concept_play": "概念炒作/题材股（游资炒作、概念热点、短期资金驱动）",
    "blue_chip": "蓝筹/价值型（稳定分红、行业龙头、护城河强）",
    "turnaround": "困境反转/ST重整（退市风险、破产重整、扭亏为盈）",
    "high_growth": "高成长型（增速高、渗透率低、产能扩张）",
    "sector_theme": "板块/产业链（行业全景、上下游分析、板块对比）",
    "macro_strategy": "宏观策略（利率、GDP、货币政策、大类资产配置）",
    # Tech subtypes
    "comparison": "技术对比（vs、比较、选哪个、替代方案）",
    "tutorial": "教程学习（怎么用、入门、指南、安装配置）",
    # Health subtypes
    "treatment": "治疗评估（疗法、药物、手术、临床）",
    "prevention": "预防保健（生活方式、饮食、运动、风险因素）",
    # Industry subtypes
    "manufacturing": "制造业（产能、供应链、成本结构）",
    "service": "服务业（平台经济、消费趋势、数字化）",
    "emerging": "新兴产业（新能源、AI、生物技术、渗透率低）",
    # Policy subtypes
    "regulation": "监管政策（法规、合规、处罚、准入门槛）",
    "incentive": "激励政策（补贴、优惠、扶持、税收减免）",
    "reform": "改革政策（体制改革、行业重组、市场化）",
    # Macro subtypes
    "monetary": "货币政策（利率、M2、社融、流动性）",
    "fiscal": "财政政策（税收、支出、赤字、国债）",
    "global": "全球宏观（汇率、贸易、地缘、IMF/世行）",
}


def _get_subtype_descriptions() -> dict:
    """Get subtype descriptions dict for prompt building."""
    return _SUBTYPE_DESCRIPTIONS


def get_all_domain_keys() -> list[str]:
    """Get all registered domain keys (for validation)."""
    return list(DOMAIN_REGISTRY.keys())


def get_valid_subtypes(domain: str) -> list[str]:
    """Get valid subtype keys for a given domain."""
    subtypes = []
    for (d, s) in SUBTYPE_CHAINS.keys():
        if d == domain:
            subtypes.append(s)
    return subtypes