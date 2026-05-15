"""
MiroThinker - Domain Registry

Central registry mapping domain names to DomainConfig instances.
Supports dynamic registration of new domains and subtypes.

Classification is now handled by the Navigator module, which generates
classification prompts dynamically from DOMAIN_REGISTRY and SUBTYPE_CHAINS.
The old hardcoded _CLASSIFY_PROMPT has been removed.
"""

import json
import httpx

from src.core.config import settings
from src.core.logging_config import logger
from src.domains.base import DomainConfig
from src.domains.finance import finance_config
from src.domains.tech import tech_config
from src.domains.health import health_config
from src.domains.general import general_config


# Domain Registry — the single source of truth for all domain configs
DOMAIN_REGISTRY: dict[str, DomainConfig] = {
    "finance": finance_config,
    "tech": tech_config,
    "health": health_config,
    "general": general_config,
}


def register_domain(name: str, config: DomainConfig):
    """Dynamically register a new domain to DOMAIN_REGISTRY.

    After registration, the Navigator will automatically include
    this domain in classification prompts — no prompt editing needed.
    """
    DOMAIN_REGISTRY[name] = config
    logger.info(f"Registered new domain: {name} ({config.name})")


def register_subtype(domain: str, subtype: str, chains: list):
    """Dynamically register a new subtype to SUBTYPE_CHAINS.

    After registration, the Navigator will automatically include
    this subtype in classification prompts for the given domain.
    """
    from src.domains.subtypes import SUBTYPE_CHAINS
    SUBTYPE_CHAINS[(domain, subtype)] = chains
    logger.info(f"Registered new subtype: {domain}/{subtype} ({len(chains)} chains)")


def get_domain_config(domain: str) -> DomainConfig:
    """Get domain configuration by name.

    Falls back to 'general' if domain is not registered.
    """
    return DOMAIN_REGISTRY.get(domain, DOMAIN_REGISTRY["general"])


# === Legacy functions (kept for backward compatibility) ===
# These delegate to the Navigator module for actual classification.

async def detect_domain(query: str, pre_search_snippets: str = "") -> str:
    """Auto-detect query domain using Navigator classification.

    DEPRECATED: Use Navigator.navigate() instead.
    Kept for backward compatibility.
    """
    from src.navigator.router import navigate
    result = await navigate(query)
    return result.domain


async def classify_domain_and_subtype(query: str, pre_search_snippets: str = "") -> dict:
    """Classify query into domain + subtype using Navigator.

    DEPRECATED: Use Navigator.navigate() instead.
    Kept for backward compatibility.

    Returns:
        {"domain": "finance", "subtype": "concept_play"} or {"domain": "general", "subtype": None}
    """
    from src.navigator.router import navigate
    result = await navigate(query)
    return {"domain": result.domain, "subtype": result.subtype}