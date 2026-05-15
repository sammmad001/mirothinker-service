"""
MiroThinker - Token Budget Allocator

Allocates token budgets and selects models based on query tier.
"""

# Default budget configuration per tier
TIER_BUDGETS = {
    "TIER_1": {
        "system_prompt_max_tokens": 1200,
        "thinking_chains": 0,  # No chains for simple queries
        "max_turns": 8,
        "context_keep": 2,
    },
    "TIER_2": {
        "system_prompt_max_tokens": 2500,
        "thinking_chains": "critical_only",
        "max_turns": 20,
        "context_keep": 5,
    },
    "TIER_3": {
        "system_prompt_max_tokens": 4000,
        "thinking_chains": "all",
        "max_turns": 35,
        "context_keep": 8,
    },
}

# Default model configuration per tier
TIER_MODELS = {
    "TIER_1": {
        "search_model": "qwen-turbo",
        "synthesis_model": "qwen-plus",
        "critic_model": None,  # Skip critic for TIER_1
    },
    "TIER_2": {
        "search_model": "qwen-turbo",
        "synthesis_model": "qwen3.6-plus",
        "critic_model": "qwen-flash",
    },
    "TIER_3": {
        "search_model": "qwen-turbo",
        "synthesis_model": "qwen3.6-plus",
        "critic_model": "qwen-flash",
    },
}


def allocate_budget(tier: str) -> dict:
    """Allocate token budget based on query tier.

    Returns a dict with system_prompt_max_tokens, thinking_chains,
    max_turns, and context_keep settings.
    """
    return TIER_BUDGETS.get(tier, TIER_BUDGETS["TIER_2"])


def select_models(tier: str, default_model: str = "qwen3.6-plus") -> dict:
    """Select models for search, synthesis, and critic based on tier.

    Args:
        tier: Query tier (TIER_1/TIER_2/TIER_3)
        default_model: Default synthesis model if not specified by user

    Returns:
        Dict with search_model, synthesis_model, critic_model
    """
    config = TIER_MODELS.get(tier, TIER_MODELS["TIER_2"]).copy()
    # Override synthesis model with user-specified default
    config["synthesis_model"] = default_model
    return config