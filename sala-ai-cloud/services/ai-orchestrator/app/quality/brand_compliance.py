"""Brand compliance validator — checks that generated HTML respects onboarding brief.

Validates:
- primary_color present in HTML/CSS
- secondary_color present
- logo_url used if provided
- font_style used
- business_name present
- sector keyword present
"""
from __future__ import annotations

import re
from typing import Any


def validate_brand_compliance(
    brief: dict[str, Any],
    design_tokens: dict[str, Any],
    generated_files: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return {score: int 0-100, issues: list[str], checks: dict}."""
    checks: dict[str, bool] = {}
    issues: list[str] = []

    # Extract expected values
    primary = (
        design_tokens.get("primary")
        or brief.get("primary_color")
        or (brief.get("brand") or {}).get("primary_color")
        or ""
    )
    secondary = (
        design_tokens.get("secondary")
        or brief.get("secondary_color")
        or (brief.get("brand") or {}).get("secondary_color")
        or ""
    )
    font_style = (
        design_tokens.get("font_heading")
        or brief.get("font_style")
        or brief.get("font_pref")
        or ""
    )
    logo_url = (
        design_tokens.get("logo_url")
        or brief.get("logo_url")
        or (brief.get("identity") or {}).get("logo_url")
        or ""
    )
    business_name = brief.get("business_name") or brief.get("name") or ""
    sector = brief.get("sector") or ""

    # Concatenate all HTML content
    all_html = ""
    for f in generated_files:
        if isinstance(f, dict) and f.get("path", "").endswith((".html", ".css", ".js")):
            all_html += (f.get("content") or "") + "\n"

    if not all_html:
        return {"score": 0, "issues": ["No HTML files found"], "checks": {}}

    # Check 1: primary color
    if primary:
        primary_lower = primary.lower()
        # Check for hex, rgb, or tailwind config
        found = primary_lower in all_html.lower() or primary_lower.replace("#", "") in all_html.lower()
        checks["primary_color"] = found
        if not found:
            issues.append(f"primary_color '{primary}' not found in generated HTML/CSS")

    # Check 2: secondary color
    if secondary:
        secondary_lower = secondary.lower()
        found = secondary_lower in all_html.lower() or secondary_lower.replace("#", "") in all_html.lower()
        checks["secondary_color"] = found
        if not found:
            issues.append(f"secondary_color '{secondary}' not found in generated HTML/CSS")

    # Check 3: logo
    if logo_url:
        found = logo_url in all_html
        checks["logo_url"] = found
        if not found:
            issues.append(f"logo_url not used in generated HTML")

    # Check 4: font
    if font_style:
        font_lower = font_style.lower()
        found = font_lower in all_html.lower() or font_lower.replace(" ", "+") in all_html.lower()
        checks["font_style"] = found
        if not found:
            issues.append(f"font_style '{font_style}' not found in generated HTML/CSS")

    # Check 5: business name
    if business_name:
        found = business_name.lower() in all_html.lower()
        checks["business_name"] = found
        if not found:
            issues.append(f"business_name '{business_name}' not found in generated HTML")

    # Check 6: sector keyword
    if sector:
        found = sector.lower() in all_html.lower()
        checks["sector"] = found
        if not found:
            issues.append(f"sector '{sector}' not mentioned in generated HTML")

    # Score calculation
    total_checks = len(checks)
    if total_checks == 0:
        score = 100
    else:
        passed = sum(1 for v in checks.values() if v)
        score = int((passed / total_checks) * 100)

    return {
        "score": score,
        "issues": issues,
        "checks": checks,
    }
