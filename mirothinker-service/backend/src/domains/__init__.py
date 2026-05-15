"""
MiroThinker - Domain Framework

Provides the Thinking Chain Directive system, Domain Registry,
and Adaptive Chain Selection for domain-specific research guidance.
"""

from src.domains.base import (
    DomainConfig,
    ThinkingChainDirective,
    SearchDirective,
    SourceSearchTemplate,
    PreSearchStrategy,
    UNIVERSAL_META_THINKING,
    format_thinking_chain,
    select_thinking_chains,
)
from src.domains.registry import (
    DOMAIN_REGISTRY,
    get_domain_config,
    detect_domain,
    classify_domain_and_subtype,
    register_domain,
    register_subtype,
)
from src.domains.adaptor import (
    compose_adaptive_chains,
    format_pivot_rules,
    format_subtype_summary,
)

# Import new domain configs
from src.domains.industry import industry_config
from src.domains.policy import policy_config
from src.domains.macro import macro_config

# Register new domains
register_domain("industry", industry_config)
register_domain("policy", policy_config)
register_domain("macro", macro_config)

__all__ = [
    # Base types
    "DomainConfig",
    "ThinkingChainDirective",
    "SearchDirective",
    "SourceSearchTemplate",
    "PreSearchStrategy",
    # Constants
    "UNIVERSAL_META_THINKING",
    "DOMAIN_REGISTRY",
    # Base functions
    "format_thinking_chain",
    "select_thinking_chains",
    "get_domain_config",
    "detect_domain",
    "classify_domain_and_subtype",
    "register_domain",
    "register_subtype",
    # Adaptive functions
    "compose_adaptive_chains",
    "format_pivot_rules",
    "format_subtype_summary",
]