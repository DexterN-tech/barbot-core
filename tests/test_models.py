"""Tests for Pydantic schema models."""

import pytest
from pydantic import ValidationError

from src.models.schemas import InventoryItem, Ingredient, Recipe, InstructionSet, InstructionStep


class TestInventoryItem:
    def test_valid_inventory_item(self) -> None:
        item = InventoryItem(
            id="inv_gin",
            name="Gin",
            category="Spirit",
            alcoholic=True,
            unit="mL",
            quantity=5000,
            aliases=["London Dry Gin"],
        )
        assert item.id == "inv_gin"
        assert item.name == "Gin"
        assert item.category == "Spirit"
        assert item.alcoholic is True
        assert item.unit == "mL"
        assert item.quantity == 5000
        assert "London Dry Gin" in item.aliases

    def test_inventory_item_defaults(self) -> None:
        item = InventoryItem(
            id="inv_ice",
            name="Ice",
            category="Other",
            alcoholic=False,
            unit="units",
            quantity=10000,
        )
        assert item.aliases == []

    def test_inventory_item_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            InventoryItem(name="Gin")  # missing id, category, unit, quantity


class TestIngredient:
    def test_valid_ingredient(self) -> None:
        ingredient = Ingredient(inventory_id="inv_gin", amount_shots=1.0)
        assert ingredient.inventory_id == "inv_gin"
        assert ingredient.amount_shots == 1.0

    def test_ingredient_negative_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Ingredient(inventory_id="inv_gin", amount_shots=-1.0)


class TestRecipe:
    def test_valid_recipe(self) -> None:
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
        assert recipe.id == "recipe_negroni"
        assert len(recipe.ingredients) == 3
        assert recipe.garnish == ["Orange Peel"]

    def test_recipe_defaults(self) -> None:
        recipe = Recipe(
            id="recipe_test",
            name="Test",
            source="Manual",
            ingredients=[Ingredient(inventory_id="inv_water", amount_shots=1.0)],
            glassware="Highball",
        )
        assert recipe.iba_verified is False
        assert recipe.garnish == []
        assert recipe.tags == []


class TestInstructionStep:
    def test_valid_fluid_dispense_step(self) -> None:
        step = InstructionStep(
            step=1,
            station="fluid_dispenser",
            action="dispense",
            payload={"inventory_id": "inv_gin", "amount_shots": 1.0},
        )
        assert step.step == 1
        assert step.station == "fluid_dispenser"

    def test_invalid_station_rejected(self) -> None:
        with pytest.raises(ValidationError):
            InstructionStep(
                step=1,
                station="invalid_station",
                action="do_something",
                payload={},
            )

    def test_all_valid_stations(self) -> None:
        valid_stations = [
            "fluid_dispenser",
            "ice_dispenser",
            "shaker_module",
            "stir_module",
            "user_prompt",
        ]
        for station in valid_stations:
            step = InstructionStep(
                step=1,
                station=station,
                action="test_action",
                payload={"test": "data"},
            )
            assert step.station == station


class TestInstructionSet:
    def test_valid_instruction_set(self) -> None:
        inst_set = InstructionSet(
            recipe_id="recipe_negroni",
            steps=[
                InstructionStep(
                    step=1,
                    station="fluid_dispenser",
                    action="dispense",
                    payload={"inventory_id": "inv_gin", "amount_shots": 1.0},
                ),
            ],
        )
        assert inst_set.recipe_id == "recipe_negroni"
        assert len(inst_set.steps) == 1
