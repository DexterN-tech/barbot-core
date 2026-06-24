"""Recipe validation pipeline.

Enforces schema correctness, inventory linkage, and IBA variance gating.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from src.models.schemas import Ingredient, InventoryItem, Recipe


class RecipeValidationError(Exception):
    """Raised when a recipe fails validation."""


def validate_recipe_schema(recipe: Recipe) -> Recipe:
    """Validate recipe against Pydantic schema.

    Returns the validated recipe or raises RecipeValidationError.
    """
    try:
        if isinstance(recipe, dict):
            recipe = Recipe.model_validate(recipe)
        return recipe
    except ValidationError as exc:
        raise RecipeValidationError(f"Schema validation failed: {exc}") from exc


def validate_inventory_linkage(
    recipe: Recipe, inventory: list[InventoryItem]
) -> dict[str, list[str]]:
    """Ensure every ingredient in the recipe has a matching inventory item.

    Returns {"missing": []} on success.

    Raises RecipeValidationError if any ingredient is missing.
    """
    inventory_ids = {item.id for item in inventory}
    missing = [
        ing.inventory_id for ing in recipe.ingredients if ing.inventory_id not in inventory_ids
    ]
    if missing:
        raise RecipeValidationError(
            f"Recipe '{recipe.id}' references missing inventory IDs: {missing}"
        )
    return {"missing": []}


def compute_iba_variance(
    recipe_ingredients: list[Ingredient],
    iba_baseline: list[dict[str, Any]],
) -> float:
    """Compute percentage variance between recipe and IBA baseline.

    Uses symmetric mean absolute percentage error across matched ingredients.
    """
    if not recipe_ingredients or not iba_baseline:
        return 0.0

    baseline_map = {b["inventory_id"]: b["amount_shots"] for b in iba_baseline}

    variances: list[float] = []
    for ing in recipe_ingredients:
        actual = ing.amount_shots
        expected = baseline_map.get(ing.inventory_id)
        if expected is None:
            continue
        if expected == 0:
            if actual == 0:
                continue
            variances.append(100.0)
        else:
            diff = abs(actual - expected) / expected
            variances.append(diff * 100.0)

    if not variances:
        return 0.0
    return sum(variances) / len(variances)


def gate_iba_variance(
    variance: float, threshold: float = 20.0
) -> tuple[str, dict[str, Any]]:
    """Apply the recipe variance gate.

    Returns (decision, details) where decision is:
      - "auto_approve" if variance <= threshold
      - "unresolved_review" if variance > threshold
    """
    if variance <= threshold:
        return "auto_approve", {"variance": variance, "threshold": threshold}
    return "unresolved_review", {
        "variance": variance,
        "threshold": threshold,
        "path": "artifacts/unresolved_recipes/",
    }


def validate_recipe(
    recipe: Recipe,
    inventory: list[InventoryItem],
    iba_baseline: list[dict[str, Any]] | None = None,
    variance_threshold: float = 20.0,
) -> dict[str, Any]:
    """Run full validation pipeline on a single recipe.

    Returns a result dict with schema_valid, inventory_linked, variance, variance_decision.
    """
    recipe = validate_recipe_schema(recipe)
    linkage = validate_inventory_linkage(recipe, inventory)

    variance = 0.0
    variance_decision = "auto_approve"
    if iba_baseline is not None:
        variance = compute_iba_variance(recipe.ingredients, iba_baseline)
        variance_decision, _ = gate_iba_variance(variance, threshold=variance_threshold)

    return {
        "schema_valid": True,
        "inventory_linked": True,
        "variance": variance,
        "variance_decision": variance_decision,
        "missing_inventory": linkage["missing"],
    }
