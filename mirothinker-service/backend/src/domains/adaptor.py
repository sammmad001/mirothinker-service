"""
MiroThinker - Adaptive Thinking Chain Selector

After LLM classification (domain + subtype), composes the final set of
thinking chains by merging base domain chains with subtype supplement chains.
The subtype is now determined by LLM (qwen-flash) instead of keyword matching.

Flow:
  query → LLM classify (domain+subtype) → pre_search → compose_chains
"""

from src.domains.base import (
    ThinkingChainDirective,
    format_thinking_chain,
    select_thinking_chains,
    UNIVERSAL_META_THINKING,
)
from src.domains.registry import get_domain_config
from src.domains.subtypes import SUBTYPE_CHAINS


def compose_adaptive_chains(
    domain: str,
    tier: str,
    query: str,
    pre_search_results: list[dict],
    subtype: str = None,
) -> tuple[list[ThinkingChainDirective], str]:
    """Compose the final set of thinking chains adaptively.

    Combines:
    1. Base domain chains (filtered by tier)
    2. Entity subtype supplement chains (based on LLM-provided subtype)
    3. Returns the combined chains and the subtype for logging

    Args:
        domain: Detected domain (finance/tech/health/general)
        tier: Query tier (TIER_1/TIER_2/TIER_3)
        query: The original query
        pre_search_results: Results from pre-search phase
        subtype: Subtype key from LLM classification (e.g., "concept_play", "blue_chip")

    Returns:
        (chains, subtype_key) tuple
    """
    config = get_domain_config(domain)

    # 1. Base chains filtered by tier
    base_chains = select_thinking_chains(config.thinking_chains, tier)

    # 2. Get supplement chains for the subtype (now provided by LLM)
    supplement_chains = []
    if subtype:
        key = (domain, subtype)
        if key in SUBTYPE_CHAINS:
            # For TIER_2, only include critical supplement chains
            all_supplements = SUBTYPE_CHAINS[key]
            if tier == "TIER_2":
                supplement_chains = [c for c in all_supplements if c.importance == "critical"]
            elif tier == "TIER_3":
                supplement_chains = all_supplements
            # TIER_1 gets no supplement chains

    # 3. Merge: insert supplement chains at their section_order position
    # and mark them to distinguish from base chains
    merged = list(base_chains)
    for chain in supplement_chains:
        chain_copy = ThinkingChainDirective(
            section_id=chain.section_id,
            section_title=chain.section_title,
            section_order=chain.section_order,
            importance=chain.importance,
            search_directives=chain.search_directives,
            analysis_logic=chain.analysis_logic,
            verification_rules=chain.verification_rules,
            pitfall_warnings=chain.pitfall_warnings,
            output_template=chain.output_template,
        )
        merged.append(chain_copy)

    # Sort by section_order so supplement chains appear in the right position
    merged.sort(key=lambda c: c.section_order)

    return merged, subtype


def format_pivot_rules(domain: str, subtype: str = None) -> str:
    """Generate mid-research pivot rules based on domain and subtype.

    These rules tell the LLM to adapt its search strategy when it
    discovers unexpected information during research.
    """
    pivot_rules = """## PIVOT RULES (动态调整 — 当研究发现与初始假设矛盾时)

如果在研究过程中发现以下情况，你**必须调整搜索方向**：

1. **发现隐藏概念** — 如果搜索公司名只返回传统业务信息，但进一步搜索发现转型/概念炒作，
   必须立即搜索该概念的具体细节（转型进展、资金流向、公告详情）
2. **发现矛盾信息** — 如果不同来源给出矛盾数据，必须额外搜索验证
3. **发现重要遗漏** — 如果某个关键章节找不到数据，必须换搜索词重试
4. **发现风险信号** — 如果发现诉讼/处罚/减持等负面信息，必须深入搜索详情

当发生Pivot时，在搜索中标注 [PIVOT] 并说明原因。"""

    # Domain-specific pivot triggers
    if domain == "finance":
        pivot_rules += """

### 金融领域Pivot触发器：
- 搜索结果出现"概念股"/"转型"/"算力"等词 → 立即搜索该概念的详细进展
- 搜索结果出现"ST"/"退市风险" → 立即搜索重整方案和退市标准
- 搜索结果出现"大股东减持"/"质押" → 立即搜索质押比例和减持计划
- 发现公司主营仅占营收极小比例 → 必须搜索实际主要收入来源"""

        if subtype == "concept_play":
            pivot_rules += """
- 如果发现概念已经退潮（搜索结果中负面增多）→ 必须增加风险警告权重
- 如果发现公司否认相关概念 → 必须在报告中明确标注"公司否认" """

        elif subtype == "blue_chip":
            pivot_rules += """
- 如果发现护城河被侵蚀的证据 → 必须搜索侵蚀程度和竞争对手进展
- 如果发现分红率异常下降 → 必须搜索原因（利润下滑/再投资需求）"""

    elif domain == "tech":
        pivot_rules += """

### 技术领域Pivot触发器：
- 发现官方文档与社区评价不一致 → 必须搜索更多独立评测
- 发现已废弃的API仍在广泛使用 → 必须搜索迁移路径
- 发现安全隐患或重大Bug → 必须搜索影响范围和修复状态"""

    elif domain == "health":
        pivot_rules += """

### 医学领域Pivot触发器：
- 发现研究被撤稿 → 必须搜索撤稿原因和影响
- 发现利益冲突 → 必须搜索独立验证的研究
- 发现副作用比预期严重 → 必须搜索最新安全通告"""

    elif domain == "industry":
        pivot_rules += """

### 产业领域Pivot触发器：
- 发现产业链关键环节有进口依赖 → 必须搜索国产替代进展
- 发现行业集中度突然变化 → 必须搜索并购/新进入者信息
- 发现政策重大调整 → 必须搜索受影响企业名单"""

    elif domain == "policy":
        pivot_rules += """

### 政策领域Pivot触发器：
- 发现政策有实施细则但原文未提及 → 必须搜索细则内容
- 发现利益方强烈反对 → 必须搜索反对理由和博弈走向
- 发现政策执行走样 → 必须搜索实际执行vs政策原文的差异"""

    elif domain == "macro":
        pivot_rules += """

### 宏观领域Pivot触发器：
- 发现核心数据与预期大幅偏离 → 必须搜索原因和后续影响
- 发现政策信号与市场预期不一致 → 必须搜索政策意图解读
- 发现外部冲击（地缘/能源/疫情）→ 必须搜索传导路径和影响程度"""

    return pivot_rules


def format_subtype_summary(domain: str, subtype: str) -> str:
    """Generate a brief summary of the detected subtype for the system prompt."""
    subtype_names = {
        # Finance subtypes
        "concept_play": "概念炒作型",
        "blue_chip": "蓝筹价值型",
        "turnaround": "困境反转型",
        "high_growth": "高成长型",
        "sector_theme": "板块主题型",
        "macro_strategy": "宏观策略型",
        # Tech subtypes
        "comparison": "技术对比型",
        "tutorial": "教程学习型",
        # Health subtypes
        "treatment": "治疗评估型",
        "prevention": "预防保健型",
        # Industry subtypes
        "manufacturing": "制造业型",
        "service": "服务业型",
        "emerging": "新兴产业型",
        # Policy subtypes
        "regulation": "监管政策型",
        "incentive": "激励政策型",
        "reform": "改革政策型",
        # Macro subtypes
        "monetary": "货币政策型",
        "fiscal": "财政政策型",
        "global": "全球宏观型",
    }

    name = subtype_names.get(subtype, subtype)
    return f"\n## 实体类型识别\n本次分析对象被识别为: **{name}** ({subtype})\n已针对该类型注入专属分析维度和搜索指令。\n"
