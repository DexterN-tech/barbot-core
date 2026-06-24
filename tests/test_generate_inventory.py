"""Tests for inventory generation."""

import pytest

from src.models.schemas import InventoryItem
from src.scripts.normalization.generate_inventory import generate_inventory


class TestGenerateInventory:
    def test_existing_inventory_preserved(self) -> None:
        existing = [
            InventoryItem(
                id="inv_gin",
                name="Gin",
                category="Spirit",
                alcoholic=True,
                unit="mL",
                quantity=5000,
            )
        ]
        new_names = ["Gin", "Campari"]
        result_existing, result_new = generate_inventory(existing, new_names)
        assert len(result_existing) == 2
        assert any(item.id == "inv_gin" for item in result_existing)
        assert len(result_new) == 0

    def test_new_ingredients_generated(self) -> None:
        existing: list[InventoryItem] = []
        new_names = ["Tequila", "Vodka"]
        result_existing, result_new = generate_inventory(existing, new_names)
        assert len(result_existing) == 2
        assert set(item.name for item in result_existing) == {"Tequila", "Vodka"}
        assert len(result_new) == 0

    def test_no_duplicates_generated(self) -> None:
        existing = [
            InventoryItem(
                id="inv_gin",
                name="Gin",
                category="Spirit",
                alcoholic=True,
                unit="mL",
                quantity=5000,
            )
        ]
        new_names = ["Gin", "Gin", "Campari"]
        result_existing, result_new = generate_inventory(existing, new_names)
        assert len(result_existing) == 2
        assert any(item.id == "inv_gin" for item in result_existing)
        assert result_new == []

    def test_empty_inputs(self) -> None:
        existing: list[InventoryItem] = []
        new_names: list[str] = []
        result_existing, result_new = generate_inventory(existing, new_names)
        assert result_existing == []
        assert result_new == []