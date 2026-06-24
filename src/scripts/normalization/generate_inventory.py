"""Inventory generation.

Expands the inventory list deterministically by merging new ingredient names
against the existing inventory without overwriting or deleting entries.
"""

from typing import Sequence

from src.models.schemas import InventoryItem
from src.scripts.normalization.normalize_ingredients import normalize_ingredient


def generate_inventory(
    existing: Sequence[InventoryItem],
    new_names: Sequence[str],
    category_default: str = "Other",
    unit_default: str = "mL",
    quantity_default: int = 1000,
) -> tuple[list[InventoryItem], list[str]]:
    """Merge new ingredient names into inventory.

    Returns:
        (merged_inventory, unresolved_names)

        * merged_inventory: existing inventory augmented with new entries
          for any names not already present.
        * unresolved_names: new names that could not be mapped (should be
          empty for normal operation).
    """
    normalized_existing = {normalize_ingredient(item.name): item for item in existing}
    merged = list(existing)
    unresolved: list[str] = []
    seen = set(normalized_existing)
    next_index = len(existing) + 1

    for raw_name in new_names:
        canonical = normalize_ingredient(raw_name)
        if not canonical:
            unresolved.append(raw_name)
            continue
        if canonical in seen:
            continue
        new_entry = InventoryItem(
            id=f"inv_{canonical.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_')}_{next_index}",
            name=canonical,
            category=category_default,
            alcoholic=False,
            unit=unit_default,
            quantity=quantity_default,
        )
        merged.append(new_entry)
        seen.add(canonical)
        next_index += 1

    return merged, unresolved