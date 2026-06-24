"""Tests for data file integrity across recipes, inventory, and instruction sets."""

import json
from pathlib import Path

import pytest

from src.models.schemas import Ingredient, InventoryItem, Recipe, InstructionSet
from src.scripts.validation.validate_recipes import (
    RecipeValidationError,
    validate_inventory_linkage,
    validate_recipe_schema,
)


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class TestDataFileIntegrity:
    def test_recipes_json_has_schema_version(self) -> None:
        data = load_json(DATA_DIR / "RECIPES.json")
        assert data["schema_version"] == "1.0.0"

    def test_inventory_json_has_schema_version(self) -> None:
        data = load_json(DATA_DIR / "INVENTORY.json")
        assert data["schema_version"] == "1.0.0"

    def test_instruction_sets_json_has_schema_version(self) -> None:
        data = load_json(DATA_DIR / "INSTRUCTION_SETS.json")
        assert data["schema_version"] == "1.0.0"

    def test_all_recipes_have_unique_ids(self) -> None:
        data = load_json(DATA_DIR / "RECIPES.json")
        ids = [r["id"] for r in data["recipes"]]
        assert len(ids) == len(set(ids))

    def test_all_inventory_has_unique_ids(self) -> None:
        data = load_json(DATA_DIR / "INVENTORY.json")
        ids = [i["id"] for i in data["inventory"]]
        assert len(ids) == len(set(ids))

    def test_all_ingredients_link_to_inventory(self) -> None:
        recipes_data = load_json(DATA_DIR / "RECIPES.json")
        inventory_data = load_json(DATA_DIR / "INVENTORY.json")
        inventory_ids = {i["id"] for i in inventory_data["inventory"]}
        for recipe in recipes_data["recipes"]:
            for ing in recipe["ingredients"]:
                assert ing["inventory_id"] in inventory_ids, (
                    f"Recipe {recipe['id']} references missing inventory {ing['inventory_id']}"
                )

    def test_every_recipe_has_instruction_set(self) -> None:
        recipes_data = load_json(DATA_DIR / "RECIPES.json")
        instructions_data = load_json(DATA_DIR / "INSTRUCTION_SETS.json")
        recipe_ids = {r["id"] for r in recipes_data["recipes"]}
        instruction_recipe_ids = {i["recipe_id"] for i in instructions_data["instruction_sets"]}
        missing = recipe_ids - instruction_recipe_ids
        assert not missing, f"Recipes missing instruction sets: {missing}"

    def test_recipe_schemas_are_valid(self) -> None:
        data = load_json(DATA_DIR / "RECIPES.json")
        for recipe in data["recipes"]:
            validate_recipe_schema(recipe)

    def test_inventory_schemas_are_valid(self) -> None:
        data = load_json(DATA_DIR / "INVENTORY.json")
        for item in data["inventory"]:
            InventoryItem.model_validate(item)

    def test_instruction_set_schemas_are_valid(self) -> None:
        data = load_json(DATA_DIR / "INSTRUCTION_SETS.json")
        for inst in data["instruction_sets"]:
            InstructionSet.model_validate(inst)
