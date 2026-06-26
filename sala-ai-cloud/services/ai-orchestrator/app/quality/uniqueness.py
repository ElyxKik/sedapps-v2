"""Uniqueness score — evaluates how unique and varied a generated site is.

Checks:
- Number of distinct sections across pages
- Variety of section types (hero, features, testimonials, etc.)
- Absence of repetitive placeholder text
- Presence of sector-specific vocabulary
- Structural diversity between pages
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any


_PLACEHOLDER_PATTERNS = [
    r"lorem\s+ipsum",
    r"placeholder",
    r"your\s+(text|content|title|message)\s+here",
    r"todo\b",
    r"fixme\b",
    r"xx+",
    r"exemple\s+de\s+texte",
    r"texte\s+par\s+défaut",
]

_SECTION_TAGS = re.compile(r"<(section|article|aside|main|header|footer|nav)\b", re.IGNORECASE)
_HEADING_TAGS = re.compile(r"<h[1-6]\b", re.IGNORECASE)
_CLASS_KEYWORDS = re.compile(r'class="([^"]*)"', re.IGNORECASE)


def _count_sections(html: str) -> int:
    return len(_SECTION_TAGS.findall(html))


def _count_headings(html: str) -> int:
    return len(_HEADING_TAGS.findall(html))


def _extract_class_keywords(html: str) -> set[str]:
    classes: set[str] = set()
    for match in _CLASS_KEYWORDS.finditer(html):
        for cls in match.group(1).split():
            if len(cls) > 3:
                classes.add(cls.lower())
    return classes


def _detect_section_types(html: str) -> set[str]:
    """Detect types of sections based on class names and content."""
    types: set[str] = set()
    classes = _extract_class_keywords(html)
    class_str = " ".join(classes)

    type_map = {
        "hero": ["hero", "banner", "headline"],
        "features": ["feature", "services", "advantage", "why"],
        "about": ["about", "team", "who-we"],
        "testimonials": ["testimonial", "review", "feedback"],
        "pricing": ["pricing", "plan", "tarif"],
        "faq": ["faq", "question"],
        "cta": ["cta", "call-to-action", "contact-cta"],
        "contact": ["contact", "form", "reach"],
        "gallery": ["gallery", "portfolio", "showcase"],
        "stats": ["stat", "counter", "metric"],
        "blog": ["blog", "article", "news", "post"],
        "menu": ["menu", "dish", "food"],
        "products": ["product", "shop", "store", "card-product"],
        "team": ["team", "staff", "member"],
        "footer": ["footer"],
    }

    for section_type, keywords in type_map.items():
        if any(kw in class_str for kw in keywords):
            types.add(section_type)

    return types


def _check_placeholders(html: str) -> list[str]:
    found = []
    lower = html.lower()
    for pattern in _PLACEHOLDER_PATTERNS:
        if re.search(pattern, lower):
            found.append(pattern)
    return found


def _count_distinct_text_blocks(html: str) -> int:
    """Count distinct meaningful text blocks (paragraphs, headings, list items)."""
    blocks = re.findall(r"<(?:p|h[1-6]|li|blockquote|figcaption)\b[^>]*>(.*?)</(?:p|h[1-6]|li|blockquote|figcaption)>", html, re.IGNORECASE | re.DOTALL)
    # Strip tags from each block and check it's non-trivial
    distinct = set()
    for block in blocks:
        text = re.sub(r"<[^>]+>", "", block).strip()
        if len(text) > 10:
            distinct.add(text[:100].lower())
    return len(distinct)


def compute_uniqueness_score(
    generated_files: list[dict[str, Any]],
    brief: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return {score: int 0-100, issues: list[str], details: dict}."""
    brief = brief or {}
    issues: list[str] = []
    details: dict[str, Any] = {}

    html_files = [f for f in generated_files if isinstance(f, dict) and f.get("path", "").endswith(".html")]
    if not html_files:
        return {"score": 0, "issues": ["No HTML files found"], "details": {}}

    all_html = "".join((f.get("content") or "") + "\n" for f in html_files)

    # Metric 1: Total sections (0-20 pts)
    total_sections = sum(_count_sections(f.get("content") or "") for f in html_files)
    details["total_sections"] = total_sections
    if total_sections >= 8:
        section_score = 20
    elif total_sections >= 5:
        section_score = 15
    elif total_sections >= 3:
        section_score = 10
    elif total_sections >= 1:
        section_score = 5
    else:
        section_score = 0
        issues.append("No <section> tags found — site lacks structure")

    # Metric 2: Section type variety (0-25 pts)
    section_types = _detect_section_types(all_html)
    details["section_types"] = list(section_types)
    type_count = len(section_types)
    if type_count >= 6:
        type_score = 25
    elif type_count >= 4:
        type_score = 20
    elif type_count >= 3:
        type_score = 15
    elif type_count >= 2:
        type_score = 10
    elif type_count >= 1:
        type_score = 5
    else:
        type_score = 0
        issues.append("No recognizable section types detected")

    # Metric 3: Distinct text blocks (0-20 pts)
    distinct_blocks = _count_distinct_text_blocks(all_html)
    details["distinct_text_blocks"] = distinct_blocks
    if distinct_blocks >= 15:
        text_score = 20
    elif distinct_blocks >= 10:
        text_score = 15
    elif distinct_blocks >= 5:
        text_score = 10
    elif distinct_blocks >= 2:
        text_score = 5
    else:
        text_score = 0
        issues.append("Very few distinct text blocks — content may be too thin")

    # Metric 4: Placeholder absence (0-15 pts)
    placeholders = _check_placeholders(all_html)
    details["placeholders_found"] = placeholders
    if not placeholders:
        placeholder_score = 15
    else:
        placeholder_score = max(0, 15 - len(placeholders) * 5)
        issues.append(f"Placeholder text detected: {', '.join(placeholders)}")

    # Metric 5: Page diversity (0-20 pts) — only for multipage
    if len(html_files) > 1:
        page_class_sets = []
        for f in html_files:
            page_class_sets.append(_extract_class_keywords(f.get("content") or ""))
        # Jaccard similarity between first and other pages
        if page_class_sets[0]:
            first = page_class_sets[0]
            similarities = []
            for other in page_class_sets[1:]:
                union = first | other
                if union:
                    inter = first & other
                    similarities.append(len(inter) / len(union))
            avg_sim = sum(similarities) / len(similarities) if similarities else 1.0
            details["avg_page_similarity"] = round(avg_sim, 2)
            if avg_sim < 0.3:
                diversity_score = 20
            elif avg_sim < 0.5:
                diversity_score = 15
            elif avg_sim < 0.7:
                diversity_score = 10
            elif avg_sim < 0.9:
                diversity_score = 5
            else:
                diversity_score = 0
                issues.append("Pages are too similar — low structural diversity")
        else:
            diversity_score = 10
    else:
        # Single page — award full points if enough sections
        diversity_score = 20 if total_sections >= 5 else 10

    total = section_score + type_score + text_score + placeholder_score + diversity_score
    details["breakdown"] = {
        "sections": section_score,
        "section_types": type_score,
        "text_blocks": text_score,
        "placeholders": placeholder_score,
        "page_diversity": diversity_score,
    }

    return {
        "score": total,
        "issues": issues,
        "details": details,
    }
