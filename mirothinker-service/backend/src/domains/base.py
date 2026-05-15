"""
MiroThinker - Domain Framework Base Classes

Defines the core data structures for the Thinking Chain Directive system
and Universal Meta-Thinking Rules shared across all domains.
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SearchDirective:
    """A single search query directive within a thinking chain."""
    query_template: str       # e.g., "{query} 年报 财务数据 三张表"
    purpose: str              # e.g., "获取3-5年财务数据"
    required: bool = True
    fallback_queries: list[str] = field(default_factory=list)


@dataclass
class ThinkingChainDirective:
    """A thinking chain directive for one section of the research report.

    Each directive tells the LLM:
    - WHAT to search for (search_directives)
    - HOW to analyze the data (analysis_logic)
    - WHAT to verify (verification_rules)
    - WHAT to avoid (pitfall_warnings)
    - HOW to present (output_template)
    """
    section_id: str           # e.g., "fin_05_financial_analysis"
    section_title: str        # e.g., "五、财务分析"
    section_order: int        # Ordering in the final output
    importance: str           # "critical" / "important" / "supplementary"
    search_directives: list[SearchDirective]
    analysis_logic: list[str]
    verification_rules: list[str]
    pitfall_warnings: list[str]
    output_template: str


@dataclass
class SourceSearchTemplate:
    """A domain-specific source search template for pre-search phase."""
    name: str
    query_template: str       # e.g., "site:cninfo.com.cn {query} 公告"
    priority: str             # "highest" / "high" / "medium"
    max_results: int = 3


@dataclass
class PreSearchStrategy:
    """Pre-search strategy for seeding context before autonomous research."""
    mandatory_angle_queries: list[str]     # Templates with {query}/{current_year}
    source_search_templates: list[SourceSearchTemplate]
    recency_preference: str = "y"          # "d"/"w"/"m"/"y"/None


@dataclass
class DomainConfig:
    """Complete configuration for a research domain.

    Encapsulates all domain-specific logic: thinking chains, search strategies,
    quality checks, critic templates, output formats, and analysis methodology.
    """
    name: str
    keywords: list[str]
    thinking_chains: list[ThinkingChainDirective]
    pre_search_strategy: PreSearchStrategy
    quality_checks: list[Callable]
    critic_template: str
    output_template: str
    max_directive_tokens: int = 3000
    analysis_methodology: str = ""  # Phase 4: Domain-specific analysis methodology


# === Universal Meta-Thinking Rules ===
# Shared across ALL domains, injected into every system prompt.

UNIVERSAL_META_THINKING = """## META-THINKING RULES (Universal — MUST follow for ALL domains)
1. NEVER answer based on a single perspective — seek at least 2 independent sources
2. ALWAYS search for CONTRADICTING evidence before forming a conclusion
3. ALWAYS verify key claims across MULTIPLE sources (minimum 2 for any key claim)
4. ALWAYS mark UNCERTAINTY: distinguish "已确认" vs "推测" vs "有争议"
5. ALWAYS check TIMELINESS: flag any data older than 2 years as potentially outdated
6. ALWAYS consider SECOND-ORDER effects: what are the indirect consequences?
7. ALWAYS present the strongest OPPOSING argument alongside your main thesis"""


def format_thinking_chain(chain: ThinkingChainDirective, query: str = "") -> str:
    """Render a thinking chain directive into a structured prompt section.

    Expanded format: retains more analysis logic and warnings for deeper reasoning.
    Structure: title → search queries → analysis logic (top 5) → warnings (top 3).
    Multi-line format for better LLM comprehension.
    """
    parts = [f"## {chain.section_title}"]

    # === SEARCH: query templates ===
    if chain.search_directives:
        queries = []
        for sd in chain.search_directives[:3]:  # Max 3 queries
            q = sd.query_template.replace("{query}", query) if query else sd.query_template
            queries.append(q)
        parts.append("搜:" + " | ".join(f'"{q}"' for q in queries))

    # === LOGIC: top 5 analysis points (was top 2) ===
    if chain.analysis_logic:
        logic_points = chain.analysis_logic[:5]
        parts.append("析:" + " | ".join(logic_points))

    # === WARNINGS: top 3 pitfalls (was top 1) ===
    if chain.pitfall_warnings:
        warnings = chain.pitfall_warnings[:3]
        parts.append("警:" + " | ".join(warnings))

    return "\n".join(parts)


def select_thinking_chains(
    chains: list[ThinkingChainDirective],
    tier: str = "TIER_3",
) -> list[ThinkingChainDirective]:
    """Select thinking chains based on query tier for token efficiency.

    TIER_1 (Simple): No thinking chains, just meta-thinking rules
    TIER_2 (Medium): Critical chains only
    TIER_3 (Deep): All chains
    """
    if tier == "TIER_1":
        return []

    if tier == "TIER_2":
        return [c for c in chains if c.importance == "critical"]

    # TIER_3: all chains
    return chains
