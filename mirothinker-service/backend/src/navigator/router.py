"""
MiroThinker - Navigator Agent

The routing/navigation layer that classifies queries, selects
analysis frameworks, and allocates token budgets. Single entry point
for all routing decisions.

Architecture:
  User Query → navigate(query) → RoutingResult → ResearchExecutor
"""

import json
import httpx

from dataclasses import dataclass, field
from typing import Optional

from src.core.config import settings
from src.core.logging_config import logger
from src.navigator.classify_prompt_builder import (
    build_classify_prompt,
    get_all_domain_keys,
    get_valid_subtypes,
)
from src.navigator.budget_allocator import allocate_budget, select_models
from src.domains.registry import DOMAIN_REGISTRY
from src.domains.subtypes import SUBTYPE_CHAINS


@dataclass
class RoutingResult:
    """Complete routing result from Navigator.

    Contains all decisions needed by ResearchExecutor:
    - tier, domain, subtype: classification results
    - budget_config: token budget allocation
    - model_config: model selection for each phase
    """
    tier: str
    domain: str
    subtype: Optional[str] = None
    budget_config: dict = field(default_factory=dict)
    model_config: dict = field(default_factory=dict)


async def navigate(
    query: str,
    default_model: str = "qwen3.6-plus",
) -> RoutingResult:
    """Navigator main entry point — single LLM call for classification + routing.

    Replaces the previous classify_and_route() + classify_domain_and_subtype()
    dual-call pattern with a single qwen-flash call using dynamically
    generated classification prompt.

    Args:
        query: The user's research query
        default_model: Default synthesis model (overridable by user)

    Returns:
        RoutingResult with tier, domain, subtype, budget, and model config
    """
    # 1. Build classification prompt dynamically
    prompt = build_classify_prompt(query)

    # 2. Single qwen-flash call for classification
    classification = await _classify_with_llm(prompt)

    tier = classification.get("tier", "TIER_2")
    domain = classification.get("domain", "general")
    subtype = classification.get("subtype")

    # 3. Allocate budget and select models based on tier
    budget_config = allocate_budget(tier)
    model_config = select_models(tier, default_model)

    # 4. Log routing result
    logger.info(
        f"Navigator routing: query='{query[:30]}...' → "
        f"tier={tier}, domain={domain}, subtype={subtype}"
    )

    return RoutingResult(
        tier=tier,
        domain=domain,
        subtype=subtype,
        budget_config=budget_config,
        model_config=model_config,
    )


async def _classify_with_llm(prompt: str) -> dict:
    """Internal: call qwen-flash for classification.

    Returns parsed classification dict or default fallback.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.DASHSCOPE_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen-flash",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 100,
                },
                timeout=30,
            )

            if resp.status_code != 200:
                logger.warning(f"Navigator classification API error: {resp.status_code}")
                return _default_routing()

            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Parse JSON from response (handle markdown code block wrapping)
            if "```" in content:
                parts = content.split("```")
                for part in parts:
                    clean = part.strip()
                    if clean.startswith("json"):
                        clean = clean[4:].strip()
                    if clean.startswith("{"):
                        content = clean
                        break

            result = json.loads(content)

            # Validate tier
            tier = result.get("tier", "TIER_2")
            if tier not in ("TIER_1", "TIER_2", "TIER_3"):
                logger.warning(f"Invalid tier: {tier}, falling back to TIER_2")
                tier = "TIER_2"

            # Validate domain (dynamic — check against DOMAIN_REGISTRY)
            domain = result.get("domain", "general")
            valid_domains = get_all_domain_keys()
            if domain not in valid_domains:
                logger.warning(f"Navigator returned unknown domain: {domain}, falling back to general")
                domain = "general"

            # Validate subtype (dynamic — check against SUBTYPE_CHAINS)
            subtype = result.get("subtype")
            if subtype and not isinstance(subtype, str):
                subtype = None
            if subtype:
                valid_subtypes = get_valid_subtypes(domain)
                if valid_subtypes and subtype not in valid_subtypes:
                    logger.warning(f"Invalid subtype {subtype} for domain {domain}, setting to None")
                    subtype = None

            return {"tier": tier, "domain": domain, "subtype": subtype}

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse Navigator response: {e}")
        return _default_routing()
    except Exception as e:
        logger.warning(f"Navigator classification failed: {e}")
        return _default_routing()


def _default_routing() -> dict:
    """Default fallback routing result."""
    return {"tier": "TIER_2", "domain": "general", "subtype": None}