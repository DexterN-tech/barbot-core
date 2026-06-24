"""Tests for recipe validation pipeline."""

from typing import Any

import pytest
from pydantic import ValidationError

from src.models.schemas import Ingredient, InventoryItem, Recipe, InstructionSet
from src.scripts.validation.validate_recipes import (
    RecipeValidationError,
    validate_recipe_schema,
    validate_inventory_linkage,
    compute_iba_variance,
    gate_iba_variance,
    validate_recipe,
)


class TestValidateRecipeSchema:
    def test_valid_schema_passes(self) -> None:
        recipe = Recipe(
            id="recipe_test",
            name="Test",
            source="IBA",
            ingredients=[Ingredient(inventory_id="inv_gin", amount_shots=1.0)],
            glassware="Rocks",
        )
        result = validate_recipe_schema(recipe)
        assert result is recipe

    def test_missing_required_fields_raises(self) -> None:
        with pytest.raises(RecipeValidationError):
            validate_recipe_schema({
                "id": "",
                "name": "Test",
                "source": "IBA",
                "glassware": "Rocks",
            })

    def test_negative_amount_raises(self) -> None:
        with pytest.raises(RecipeValidationError):
            validate_recipe_schema({
                "id": "recipe_test",
                "name": "Test",
                "source": "IBA",
                "ingredients": [{"inventory_id": "inv_gin", "amount_shots": -1.0}],
                "glassware": "Rocks",
            })


class TestValidateInventoryLinkage:
    def test_all_ingredients_linked(self) -> None:
        recipe = Recipe(
            id="recipe_test",
            name="Test",
            source="IBA",
            ingredients=[
                Ingredient(inventory_id="inv_gin", amount_shots=1.0),
                Ingredient(inventory_id="inv_campari", amount_shots=1.0),
            ],
            glassware="Rocks",
        )
        inventory = [
            InventoryItem(id="inv_gin", name="Gin", category="Spirit", alcoholic=True, unit="mL", quantity=1000),
            InventoryItem(id="inv_campari", name="Campari", category="Bitter Aperitif", alcoholic=True, unit="mL", quantity=1000),
        ]
        result = validate_inventory_linkage(recipe, inventory)
        assert result["missing"] == []

    def test_missing_inventory_detected(self) -> None:
        recipe = Recipe(
            id="recipe_test",
            name="Test",
            source="IBA",
            ingredients=[Ingredient(inventory_id="inv_gin", amount_shots=1.0)],
            glassware="Rocks",
        )
        inventory = [
            InventoryItem(id="inv_vodka", name="Vodka", category="Spirit", alcoholic=True, unit="mL", quantity=1000),
        ]
        with pytest.raises(RecipeValidationError):
            validate_inventory_linkage(recipe, inventory)


class TestComputeIbaVariance:
    def test_exact_match_zero_variance(self) -> None:
        recipe_ings = [
            Ingredient(inventory_id="inv_gin", amount_shots=1.0),
            Ingredient(inventory_id="inv_campari", amount_shots=1.0),
        ]
        baseline_ings: list[dict[str, Any]] = [
            {"inventory_id": "inv_gin", "amount_shots": 1.0},
            {"inventory_id": "inv_campari", "amount_shots": 1.0},
        ]
        variance = compute_iba_variance(recipe_ings, baseline_ings)
        assert variance == 0.0

    def test_high_variance_detected(self) -> None:
        recipe_ings = [
            Ingredient(inventory_id="inv_gin", amount_shots=2.0),
            Ingredient(inventory_id="inv_campari", amount_shots=1.0),
        ]
        baseline_ings: list[dict[str, Any]] = [
            {"inventory_id": "inv_gin", "amount_shots": 1.0},
            {"inventory_id": "inv_campari", "amount_shots": 1.0},
        ]
        variance = compute_iba_variance(recipe_ings, baseline_ings)
        assert variance == pytest.approx(50.0)

    def test_within_threshold_auto_approve(self) -> None:
        recipe_ings = [
            Ingredient(inventory_id="inv_gin", amount_shots=1.07),
            Ingredient(inventory_id="inv_campari", amount_shots=1.0),
        ]
        baseline_ings: list[dict[str, Any]] = [
            {"inventory_id": "inv_gin", "amount_shots": 1.0},
            {"inventory_id": "inv_campari", "amount_shots": 1.0},
        ]
        variance = compute_iba_variance(recipe_ings, baseline_ings)
        decision, details = gate_iba_variance(variance, threshold=20.0)
        assert decision == "auto_approve"

    def test_exceeds_threshold_routed_to_unresolved(self) -> None:
        recipe_ings = [
            Ingredient(inventory_id="inv_gin", amount_shots=2.0),
        ]
        baseline_ings: list[dict[str, Any]] = [
            {"inventory_id": "inv_gin", "amount_shots": 1.0},
        ]
        variance = compute_iba_variance(recipe_ings, baseline_ings)
        decision, details = gate_iba_variance(variance, threshold=20.0)
        assert decision == "unresolved_review"


class TestValidateRecipe:
    def test_full_validation_success(self) -> None:
        recipe = Recipe(
            id="recipe_negroni",
            name="Negroni",
            source="IBA",
            iba_verified=True,
            ingredients=[
                Ingredient(inventory_id="inv_gin", amount_shots=1.0),
                Ingredient(inventory_id="inv_campari", amount_shots=1.0),
                Ingredient(inventory_id="inv_sweet_vermouth", amount_shots=1.0),
            ],
            garnish=["Orange Peel"],
            glassware="Rocks Glass",
            tags=["Classic", "Spirit Forward"],
        )
        inventory = [
            InventoryItem(id="inv_gin", name="Gin", category="Spirit", alcoholic=True, unit="mL", quantity=1000),
            InventoryItem(id="inv_campari", name="Campari", category="Bitter Aperitif", alcoholic=True, unit="mL", quantity=1000),
            InventoryItem(id="inv_sweet_vermouth", name="Sweet Vermouth", category="Fortified Wine", alcoholic=True, unit="mL", quantity=1000),
        ]
        baseline = {
            "inventory_id": "inv_gin", "amount_shots": 1.0
        }, {
            "inventory_id": "inv_campari", "amount_shots": 1.0
        }, {
            "inventory_id": "inv_sweet_vermouth", "amount_shots": 1.0
        }
        result = validate_recipe(
            recipe,
            inventory,
            iba_baseline=list(baseline),
        )
        assert result["schema_valid"] is True
        assert result["inventory_linked"] is True
        assert result["variance_decision"] == "auto_approve"
