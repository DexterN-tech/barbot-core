"""TheCocktailDB API ingestion pipeline.

Fetches all cocktails from TheCocktailDB (key=1), normalizes ingredients,
deduplicates against existing recipes, and extends inventory automatically.

Reference: https://www.thecocktaildb.com/api.php
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Sequence

import requests

from src.models.schemas import Ingredient, InventoryItem, Recipe
from src.scripts.normalization.normalize_ingredients import normalize_ingredient


API_BASE = "https://www.thecocktaildb.com/api/json/v1/1"
API_KEY = "1"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


# =====================================================================
# Measurement Conversion
# =====================================================================
def _fraction_to_float(frac: str) -> float:
    """Convert a fraction string like '1 1/2' or '3/4' to float."""
    frac = frac.strip()
    if " " in frac:
        whole, part = frac.split(" ", 1)
        return float(whole) + _fraction_to_float(part)
    if "/" in frac:
        num, den = frac.split("/", 1)
        return float(num) / float(den)
    return float(frac)


def convert_to_shots(measure: str | None) -> float:
    """Convert a TheCocktailDB measure string to shots (1 oz ≈ 1 shot).

    Supported units:
        oz, shot -> direct 1:1 conversion (1 oz ≈ 30 mL)
        ml -> divide by 30
        cl -> divide by 3
        bottle -> 25 shots

    Raises:
        ValueError: if the unit is unknown or measure cannot be parsed.
    """
    if not measure or not measure.strip():
        return 0.0

    cleaned = measure.strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)

    unit_map: dict[str, float] = {
        "oz": 1.0,
        "shot": 1.0,
        "shots": 1.0,
        "ml": 1.0 / 30.0,
        "cl": 1.0 / 3.0,
        "bottle": 25.0,
    }

    matched_mult = None
    numeric_part = cleaned

    for unit, mult in unit_map.items():
        if cleaned.endswith(unit):
            matched_mult = mult
            numeric_part = cleaned[: -len(unit)]
            break

    if matched_mult is None:
        raise ValueError(f"Unknown measure unit in: {measure!r}")

    numeric_part = numeric_part.strip()
    if not numeric_part:
        raise ValueError(f"Missing numeric value in: {measure!r}")

    try:
        value = _fraction_to_float(numeric_part)
    except ValueError:
        raise ValueError(f"Cannot parse numeric value in: {measure!r}")

    return round(value * matched_mult, 4)


# =====================================================================
# Ingredient Extraction
# =====================================================================
def extract_ingredients(drink: dict) -> list[dict]:
    """Extract ingredient names and shot amounts from a drink dict."""
    ingredients: list[dict] = []
    for i in range(1, 16):
        raw_ing = drink.get(f"strIngredient{i}")
        raw_meas = drink.get(f"strMeasure{i}")
        if not raw_ing or not raw_ing.strip():
            continue
        if not raw_meas or not raw_meas.strip():
            continue
        try:
            shots = convert_to_shots(raw_meas)
        except ValueError:
            continue
        if shots <= 0:
            continue
        ingredients.append({
            "name": normalize_ingredient(raw_ing),
            "amount_shots": shots,
        })
    return ingredients


# =====================================================================
# ID Generation
# =====================================================================
def generate_recipe_id(name: str | None) -> str | None:
    """Generate a normalized recipe ID from a drink name."""
    if not name:
        return None
    norm = normalize_ingredient(name).lower().replace(" ", "_")
    norm = re.sub(r"[^a-z0-9_]", "", norm)
    norm = re.sub(r"_+", "_", norm).strip("_")
    if not norm:
        return None
    return f"recipe_{norm}"


# =====================================================================
# Duplicate Detection
# =====================================================================
def is_duplicate(name: str, existing_recipes: Sequence[Recipe]) -> bool:
    """Return True if a recipe with the same normalized name already exists."""
    norm = normalize_ingredient(name)
    return any(normalize_ingredient(r.name) == norm for r in existing_recipes)


# =====================================================================
# Inventory Mapping
# =====================================================================
def _inventory_lookup_index(
    inventory: list[InventoryItem],
) -> dict[str, InventoryItem]:
    """Build a lookup dict keyed by normalized name and aliases."""
    index: dict[str, InventoryItem] = {}
    for item in inventory:
        index[normalize_ingredient(item.name)] = item
        for alias in item.aliases:
            index[normalize_ingredient(alias)] = item
    return index


def map_ingredient_to_inventory(
    name: str,
    inventory: list[InventoryItem],
) -> tuple[str | None, list[InventoryItem]]:
    """Map an ingredient name to an inventory ID, creating a new entry if needed.

    Returns:
        (inventory_id, updated_inventory)
    """
    index = _inventory_lookup_index(inventory)
    norm = normalize_ingredient(name)

    if norm in index:
        inv_item = index[norm]
        return inv_item.id, inventory

    new_id = f"inv_{norm.lower().replace(' ', '_').replace('/', '_').replace('-', '_')}"
    new_item = InventoryItem(
        id=new_id,
        name=norm,
        category="Other",
        alcoholic=False,
        unit="mL",
        quantity=1000,
        aliases=[],
    )
    inventory.append(new_item)
    return new_id, inventory


# =====================================================================
# Instruction Generation
# =====================================================================
def generate_recipe_instructions(
    recipe_id: str,
    ingredients: list[tuple[str, float]],
    method: str = "built",
    ice: bool = True,
    garnish: list[str] | None = None,
    top_with: tuple[str, float] | None = None,
) -> list:
    """Generate structured instruction steps (mirrors generate_iba_data.py logic)."""
    from src.models.schemas import InstructionStep

    steps: list[dict] = []
    s = 1
    for inv_id, shots in ingredients:
        steps.append({
            "step": s,
            "station": "fluid_dispenser",
            "action": "dispense",
            "payload": {"inventory_id": inv_id, "amount_shots": shots},
        })
        s += 1

    if ice:
        steps.append({
            "step": s,
            "station": "ice_dispenser",
            "action": "add_ice",
            "payload": {"quantity_units": 1, "unit": "cubes"},
        })
        s += 1

    if method == "shaken":
        steps.append({
            "step": s,
            "station": "shaker_module",
            "action": "shake",
            "payload": {"duration_ms": 8000, "style": "hard"},
        })
        s += 1
        steps.append({
            "step": s,
            "station": "user_prompt",
            "action": "instruction",
            "payload": {"message": "Strain into glass."},
        })
        s += 1
    elif method == "stirred":
        steps.append({
            "step": s,
            "station": "user_prompt",
            "action": "instruction",
            "payload": {"message": "Stir gently."},
        })
        s += 1
    elif method == "blended":
        steps.append({
            "step": s,
            "station": "shaker_module",
            "action": "blend",
            "payload": {"duration_ms": 15000},
        })
        s += 1
        steps.append({
            "step": s,
            "station": "user_prompt",
            "action": "instruction",
            "payload": {"message": "Pour into glass."},
        })
        s += 1
    else:
        steps.append({
            "step": s,
            "station": "user_prompt",
            "action": "instruction",
            "payload": {"message": "Build in glass."},
        })
        s += 1

    if top_with:
        top_id, top_shots = top_with
        steps.append({
            "step": s,
            "station": "fluid_dispenser",
            "action": "dispense",
            "payload": {"inventory_id": top_id, "amount_shots": top_shots},
        })
        s += 1
        steps.append({
            "step": s,
            "station": "user_prompt",
            "action": "instruction",
            "payload": {"message": "Stir gently."},
        })
        s += 1

    for g in garnish or []:
        steps.append({
            "step": s,
            "station": "user_prompt",
            "action": "instruction",
            "payload": {"message": f"Garnish with {g}."},
        })
        s += 1

    return [InstructionStep(**step) for step in steps]


# =====================================================================
# Drink Processing
# =====================================================================
def process_drink(
    drink: dict,
    existing_recipes: list[Recipe],
    existing_inventory: list[InventoryItem],
) -> tuple[Recipe | None, list[InventoryItem]]:
    """Process a single TheCocktailDB drink dict.

    Returns:
        (recipe, newly_created_inventory_items)
        recipe is None if the drink is a duplicate or invalid.
    """
    name = (drink.get("strDrink") or "").strip()
    if not name:
        return None, []

    recipe_id = generate_recipe_id(name)
    if not recipe_id:
        return None, []

    if is_duplicate(name, existing_recipes):
        return None, []

    ingredients_data = extract_ingredients(drink)
    if not ingredients_data:
        return None, []

    iba = drink.get("strIBA")

    mapped_ingredients: list[Ingredient] = []
    current_inventory = list(existing_inventory)
    new_inventory_added: list[InventoryItem] = []

    for ing in ingredients_data:
        before_len = len(current_inventory)
        inv_id, current_inventory = map_ingredient_to_inventory(ing["name"], current_inventory)
        assert inv_id is not None
        new_inventory_added.extend(current_inventory[before_len:])
        mapped_ingredients.append(
            Ingredient(inventory_id=inv_id, amount_shots=ing["amount_shots"])
        )

    recipe = Recipe(
        id=recipe_id,
        name=name,
        source="TheCocktailDB",
        iba_verified=iba is not None,
        ingredients=mapped_ingredients,
        garnish=[],
        glassware=(drink.get("strGlass") or "Highball").title(),
        tags=["TheCocktailDB"],
    )

    return recipe, current_inventory


# =====================================================================
# API Fetching
# =====================================================================
def fetch_all_drinks() -> list[dict]:
    """Fetch all drinks from TheCocktailDB by iterating the alphabet."""
    all_drinks: list[dict] = []
    for letter in "abcdefghijklmnopqrstuvwxyz":
        url = f"{API_BASE}/search.php?f={letter}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        drinks = data.get("drinks") or []
        all_drinks.extend(drinks)
    return all_drinks


# =====================================================================
# Main Orchestration
# =====================================================================
def main() -> None:
    """Orchestrate full ingestion and persist to data files."""
    existing_recipes_path = OUTPUT_DIR / "RECIPES.json"
    existing_inventory_path = OUTPUT_DIR / "INVENTORY.json"
    instructions_path = OUTPUT_DIR / "INSTRUCTION_SETS.json"

    with open(existing_recipes_path, "r", encoding="utf-8") as f:
        recipes_data = json.load(f)
    existing_recipes = [Recipe.model_validate(r) for r in recipes_data.get("recipes", [])]

    with open(existing_inventory_path, "r", encoding="utf-8") as f:
        inventory_data = json.load(f)
    existing_inventory = [InventoryItem.model_validate(i) for i in inventory_data.get("inventory", [])]

    with open(instructions_path, "r", encoding="utf-8") as f:
        instructions_data = json.load(f)
    existing_instructions = instructions_data.get("instruction_sets", [])

    print(f"Loaded {len(existing_recipes)} existing recipes and {len(existing_inventory)} inventory items.")

    all_drinks = fetch_all_drinks()
    print(f"Fetched {len(all_drinks)} drinks from TheCocktailDB.")

    new_recipes: list[Recipe] = []
    current_inventory = list(existing_inventory)
    new_inventory_added: list[InventoryItem] = []
    seen_recipe_ids: set[str] = {r.id for r in existing_recipes}

    for drink in all_drinks:
        recipe, updated_inventory = process_drink(drink, existing_recipes, current_inventory)
        if recipe is None:
            continue
        if recipe.id in seen_recipe_ids:
            base_id = recipe.id
            suffix = drink.get("idDrink", "")
            recipe = recipe.model_copy(update={"id": f"{base_id}_{suffix}"})
            while recipe.id in seen_recipe_ids:
                suffix = f"{suffix}_tcdb"
                recipe = recipe.model_copy(update={"id": f"{base_id}_{suffix}"})
        added = [i for i in updated_inventory if i not in current_inventory]
        new_inventory_added.extend(added)
        current_inventory = updated_inventory
        new_recipes.append(recipe)
        existing_recipes.append(recipe)
        seen_recipe_ids.add(recipe.id)

    print(f"Added {len(new_recipes)} new recipes.")
    print(f"Added {len(new_inventory_added)} new inventory items.")

    # Merge inventory (avoid duplicates by id)
    merged_inventory = list(existing_inventory)
    seen_ids = {i.id for i in merged_inventory}
    for item in current_inventory:
        if item.id not in seen_ids:
            merged_inventory.append(item)
            seen_ids.add(item.id)

    # Save inventory
    inventory_output = {
        "schema_version": "1.0.0",
        "inventory": [i.model_dump(mode="json") for i in merged_inventory],
    }
    with open(existing_inventory_path, "w", encoding="utf-8") as f:
        json.dump(inventory_output, f, indent=2)
        f.write("\n")

    # Save recipes
    merged_recipes = list(existing_recipes)
    recipes_output = {
        "schema_version": "1.0.0",
        "recipes": [r.model_dump(mode="json") for r in merged_recipes],
    }
    with open(existing_recipes_path, "w", encoding="utf-8") as f:
        json.dump(recipes_output, f, indent=2)
        f.write("\n")

    # Generate and save instructions for new recipes
    new_instructions = list(existing_instructions)
    for recipe in new_recipes:
        ingredients_list = [(i.inventory_id, i.amount_shots) for i in recipe.ingredients]
        steps = generate_recipe_instructions(recipe.id, ingredients_list)
        new_instructions.append({
            "schema_version": "1.0.0",
            "recipe_id": recipe.id,
            "steps": [s.model_dump(mode="json") for s in steps],
        })

    instructions_output = {
        "schema_version": "1.0.0",
        "instruction_sets": new_instructions,
    }
    with open(instructions_path, "w", encoding="utf-8") as f:
        json.dump(instructions_output, f, indent=2)
        f.write("\n")

    print(f"Saved {len(merged_inventory)} inventory items.")
    print(f"Saved {len(merged_recipes)} recipes.")
    print(f"Saved {len(new_instructions)} instruction sets.")


if __name__ == "__main__":
    main()
