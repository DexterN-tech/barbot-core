"""Ingredient canonicalization.

Removes parenthetical qualifiers while preserving premium ingredient identity.
Normalizes whitespace and capitalization.
"""

import re


def normalize_ingredient(name: str) -> str:
    """Canonicalize an ingredient name.

    1. Strip leading/trailing whitespace.
    2. Title-case the full string.
    3. Remove parenthetical qualifiers (e.g. "Gin (London Dry)" -> "Gin").
    """
    if not name:
        return ""
    name = name.strip()
    if not name:
        return ""
    parts = name.split()
    title_parts = [p.capitalize() for p in parts]
    title_cased = " ".join(title_parts)
    cleaned = re.sub(r"\s*\([^)]*\)", "", title_cased)
    return cleaned.strip()