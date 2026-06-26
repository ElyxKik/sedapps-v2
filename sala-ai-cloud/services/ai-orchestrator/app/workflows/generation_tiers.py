from __future__ import annotations

from typing import Any

STANDARD_RULES: dict[str, Any] = {
    "quality_tier": "pro",
    "min_pages_onepage": 1,
    "min_pages_multipage": 3,
    "max_pages_multipage": 5,
    "motion_level": "medium",
    "qa_min_score": 75,
    "refinement_required": False,
}

PREMIUM_10K_RULES: dict[str, Any] = {
    "quality_tier": "premium_10k",
    "min_pages_onepage": 1,
    "min_pages_multipage": 5,
    "max_pages_multipage": 8,
    "motion_level": "advanced",
    "qa_min_score": 85,
    "refinement_required": True,
}


def get_generation_rules(brief: dict[str, Any]) -> dict[str, Any]:
    return PREMIUM_10K_RULES if brief.get("premium") else STANDARD_RULES
