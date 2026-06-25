"""Tests for TheCocktailDB ingestion script."""

from __future__ import annotations

import json
import math
from pathlib import Path
from unittest.mock import patch

import pytest

from src.models.schemas import InventoryItem, Recipe
from src.scripts.scraping.fetch_thecocktaildb import (
    convert_to_shots,
    extract_ingredients,
    fetch_all_drinks,
    generate_recipe_id,
    generate_recipe_instructions,
    is_duplicate,
    map_ingredient_to_inventory,
    process_drink,
)


class TestConvertToShots:
    def test_oz_integer(self) -> None:
        assert math.isclose(convert_to_shots("1 oz"), 1.0)
        assert math.isclose(convert_to_shots("2 oz"), 2.0)

    def test_oz_fraction(self) -> None:
        assert math.isclose(convert_to_shots("1/2 oz"), 0.5)
        assert math.isclose(convert_to_shots("1 1/2 oz"), 1.5)
        assert math.isclose(convert_to_shots("2 1/4 oz"), 2.25)

    def test_shot_unit(self) -> None:
        assert math.isclose(convert_to_shots("1 shot"), 1.0)
        assert math.isclose(convert_to_shots("1 1/2 shot"), 1.5)

    def test_ml_unit(self) -> None:
        assert math.isclose(convert_to_shots("30 ml"), 1.0)
        assert math.isclose(convert_to_shots("60 ml"), 2.0)
        assert math.isclose(convert_to_shots("15ml"), 0.5)

    def test_cl_unit(self) -> None:
        assert math.isclose(convert_to_shots("3 cl"), 1.0)
        assert math.isclose(convert_to_shots("4.5 cl"), 1.5)

    def test_null_empty(self) -> None:
        assert convert_to_shots(None) == 0.0
        assert convert_to_shots("") == 0.0

    def test_unknown_unit(self) -> None:
        with pytest.raises(ValueError):
            convert_to_shots("1 dash")

    def test_decimal_oz(self) -> None:
        assert math.isclose(convert_to_shots("0.5 oz"), 0.5)
        assert math.isclose(convert_to_shots("1.33 oz"), 1.33)

    def test_compound_ml_oz(self) -> None:
        assert math.isclose(convert_to_shots("70ml/2fl oz"), 2.0)


class TestExtractIngredients:
    def test_extracts_ingredients_and_measures(self) -> None:
        drink = {
            "strIngredient1": "Tequila",
            "strMeasure1": "1 1/2 oz ",
            "strIngredient2": "Triple sec",
            "strMeasure2": "1/2 oz ",
            "strIngredient3": "Lime juice",
            "strMeasure3": "1 oz ",
            "strIngredient4": "",
            "strMeasure4": "",
        }
        ingredients = extract_ingredients(drink)
        assert len(ingredients) == 3
        assert ingredients[0]["name"] == "Tequila"
        assert math.isclose(ingredients[0]["amount_shots"], 1.5)
        assert ingredients[1]["name"] == "Triple Sec"
        assert math.isclose(ingredients[1]["amount_shots"], 0.5)
        assert ingredients[2]["name"] == "Lime Juice"
        assert math.isclose(ingredients[2]["amount_shots"], 1.0)

    def test_skips_null_ingredients(self) -> None:
        drink = {
            "strIngredient1": "Tequila",
            "strMeasure1": "1 oz ",
            "strIngredient2": None,
            "strMeasure2": None,
        }
        ingredients = extract_ingredients(drink)
        assert len(ingredients) == 1

    def test_skips_empty_measure(self) -> None:
        drink = {
            "strIngredient1": "Salt",
            "strMeasure1": "",
        }
        ingredients = extract_ingredients(drink)
        assert len(ingredients) == 0


class TestGenerateRecipeId:
    def test_lowercase_and_underscore(self) -> None:
        assert generate_recipe_id("Margarita") == "recipe_margarita"

    def test_handles_spaces(self) -> None:
        assert generate_recipe_id("Sex On The Beach") == "recipe_sex_on_the_beach"

    def test_handles_special_chars(self) -> None:
        assert generate_recipe_id("God's ***") == "recipe_gods"

    def test_empty_returns_none(self) -> None:
        assert generate_recipe_id("") is None
        assert generate_recipe_id(None) is None


class TestIsDuplicate:
    def test_exact_match(self) -> None:
        existing = [
            Recipe(id="recipe_margarita", name="Margarita", source="IBA", glassware="Highball", ingredients=[])
        ]
        assert is_duplicate("Margarita", existing) is True

    def test_no_match(self) -> None:
        existing = [
            Recipe(id="recipe_margarita", name="Margarita", source="IBA", glassware="Highball", ingredients=[])
        ]
        assert is_duplicate("Cosmopolitan", existing) is False

    def test_case_insensitive(self) -> None:
        existing = [
            Recipe(id="recipe_margarita", name="Margarita", source="IBA", glassware="Highball", ingredients=[])
        ]
        assert is_duplicate("margarita", existing) is True


class TestMapIngredientToInventory:
    def test_exact_match(self) -> None:
        inventory = [
            InventoryItem(id="inv_gin", name="Gin", category="Spirit", alcoholic=True, unit="mL", quantity=3000)
        ]
        inv_id, _ = map_ingredient_to_inventory("Gin", inventory)
        assert inv_id == "inv_gin"

    def test_alias_match(self) -> None:
        inventory = [
            InventoryItem(id="inv_gin", name="Gin", category="Spirit", alcoholic=True, unit="mL", quantity=3000, aliases=["London Dry Gin"])
        ]
        inv_id, _ = map_ingredient_to_inventory("London Dry Gin", inventory)
        assert inv_id == "inv_gin"

    def test_normalized_match(self) -> None:
        inventory = [
            InventoryItem(id="inv_gin", name="Gin", category="Spirit", alcoholic=True, unit="mL", quantity=3000)
        ]
        inv_id, _ = map_ingredient_to_inventory("gin", inventory)
        assert inv_id == "inv_gin"

    def test_missing_creates_new(self) -> None:
        inventory: list[InventoryItem] = []
        inv_id, inventory = map_ingredient_to_inventory("Orange Juice", inventory)
        assert inv_id is not None
        assert len(inventory) == 1
        assert inventory[0].name == "Orange Juice"


class TestGenerateRecipeInstructions:
    def test_basic_instruction_set(self) -> None:
        instructions = generate_recipe_instructions("recipe_margarita", [("inv_tequila", 1.5), ("inv_triple_sec", 0.5)])
        assert len(instructions) >= 2
        assert instructions[0].station == "fluid_dispenser"
        assert instructions[0].action == "dispense"
        assert instructions[0].payload["inventory_id"] == "inv_tequila"

    def test_includes_ice_for_built(self) -> None:
        instructions = generate_recipe_instructions("recipe_test", [("inv_gin", 1.0)], ice=True)
        stations = [s.station for s in instructions]
        assert "ice_dispenser" in stations

    def test_includes_shake_for_shaken(self) -> None:
        instructions = generate_recipe_instructions("recipe_test", [("inv_gin", 1.0)], method="shaken")
        stations = [s.station for s in instructions]
        assert "shaker_module" in stations


class TestFetchAllDrinks:
    def test_fetches_all_letters(self) -> None:
        drinks = fetch_all_drinks()
        assert len(drinks) > 0
        first_letters = [d["strDrink"][0].upper() for d in drinks if d.get("strDrink")]
        assert len(first_letters) > 400


class TestProcessDrink:
    def test_valid_drink(self) -> None:
        drink = {
            "idDrink": "11007",
            "strDrink": "Margarita",
            "strCategory": "Ordinary Drink",
            "strAlcoholic": "Alcoholic",
            "strGlass": "Cocktail glass",
            "strIBA": "Contemporary Classics",
            "strTags": "IBA,ContemporaryClassic",
            "strIngredient1": "Tequila",
            "strMeasure1": "1 1/2 oz ",
            "strIngredient2": "Triple sec",
            "strMeasure2": "1/2 oz ",
            "strIngredient3": "Lime juice",
            "strMeasure3": "1 oz ",
            "strIngredient4": None,
            "strMeasure4": None,
        }
        existing_recipe = Recipe(
            id="recipe_margarita",
            name="Margarita",
            source="IBA",
            iba_verified=True,
            ingredients=[],
            garnish=[],
            glassware="Cocktail Glass",
            tags=[],
        )
        recipe, new_inventory = process_drink(drink, [existing_recipe], [])
        assert recipe is None
        assert len(new_inventory) == 0

    def test_new_drink(self) -> None:
        drink = {
            "idDrink": "99999",
            "strDrink": "Test Cocktail",
            "strCategory": "Ordinary Drink",
            "strAlcoholic": "Alcoholic",
            "strGlass": "Highball",
            "strIBA": None,
            "strTags": None,
            "strIngredient1": "Gin",
            "strMeasure1": "1 oz ",
            "strIngredient2": None,
            "strMeasure2": None,
        }
        existing_inventory = [
            InventoryItem(id="inv_gin", name="Gin", category="Spirit", alcoholic=True, unit="mL", quantity=3000)
        ]
        recipe, updated_inventory = process_drink(drink, [], existing_inventory)
        assert recipe is not None
        assert recipe.name == "Test Cocktail"
        assert recipe.id == "recipe_test_cocktail"
        assert len(updated_inventory) == 1

    def test_creates_missing_inventory(self) -> None:
        drink = {
            "idDrink": "99998",
            "strDrink": "Rare Ingredient Test",
            "strCategory": "Ordinary Drink",
            "strAlcoholic": "Alcoholic",
            "strGlass": "Highball",
            "strIBA": None,
            "strTags": None,
            "strIngredient1": "Rare Spirit",
            "strMeasure1": "1 oz ",
            "strIngredient2": None,
            "strMeasure2": None,
        }
        recipe, updated_inventory = process_drink(drink, [], [])
        assert recipe is not None
        assert len(updated_inventory) == 1
        assert updated_inventory[0].name == "Rare Spirit"
