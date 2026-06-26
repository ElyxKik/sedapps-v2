from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: LLMUsage
    raw: dict[str, Any]


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def clean_and_parse_json(candidate: str) -> Any:
    """Attempt to parse JSON, applying heuristics to fix common LLM formatting issues on failure."""
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Heuristic 0: Fix literal unescaped newlines inside double-quoted strings
    try:
        fixed_newlines = []
        in_string = False
        escaped = False
        for char in candidate:
            if char == '"' and not escaped:
                in_string = not in_string
                fixed_newlines.append(char)
            elif char == '\\' and in_string and not escaped:
                escaped = True
                fixed_newlines.append(char)
            elif char == '\n' and in_string:
                fixed_newlines.append('\\n')
                escaped = False
            else:
                escaped = False
                fixed_newlines.append(char)
        
        candidate_fixed = "".join(fixed_newlines)
        return json.loads(candidate_fixed)
    except json.JSONDecodeError:
        pass

    # Heuristic 1: Fix trailing commas e.g., [1, 2, ] or {"a": 1, }
    fixed = re.sub(r",(\s*[\]}])", r"\1", candidate)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Heuristic 2: LLM sometimes uses single quotes for keys/values, e.g. 'slug': 'home' or "title": 'Abia'
    # This regex attempts to target single quotes surrounding words/strings but avoids breaking apostrophes inside French text
    # (like "l'entreprise" or "l'IA").
    # We replace single quotes that are used as structural delimiters.
    fixed_quotes = fixed
    # Replace single quotes at the beginning/end of keys or values:
    # 1. 'key': -> "key":
    fixed_quotes = re.sub(r"'\s*([a-zA-Z0-9_-]+)\s*'\s*:", r'"\1":', fixed_quotes)
    # 2. : 'value' -> : "value" (avoiding inside apostrophes)
    fixed_quotes = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_quotes)
    # 3. 'value', -> "value",
    fixed_quotes = re.sub(r"'\s*,", r'",', fixed_quotes)
    # 4. , 'value' -> , "value"
    fixed_quotes = re.sub(r",\s*'([^']*)'", r', "\1"', fixed_quotes)
    # 5. [ 'value' ] -> [ "value" ]
    fixed_quotes = re.sub(r"\[\s*'([^']*)'\s*\]", r'["\1"]', fixed_quotes)

    try:
        return json.loads(fixed_quotes)
    except json.JSONDecodeError:
        pass

    # Re-raise original decode error by running standard loads
    return json.loads(candidate)


def extract_json(text: str) -> Any:
    """Try hard to extract a JSON object/array from an LLM response."""
    if not text:
        raise ValueError("empty LLM response")

    # 1. fenced code block
    m = _JSON_FENCE_RE.search(text)
    if m:
        candidate = m.group(1).strip()
        try:
            return clean_and_parse_json(candidate)
        except json.JSONDecodeError:
            pass

    # 2. first { ... last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return clean_and_parse_json(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    # 3. first [ ... last ]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return clean_and_parse_json(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"could not parse JSON from LLM response: {text[:200]}...")
