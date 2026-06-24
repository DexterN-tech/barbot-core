"""Tests for ingredient normalization."""

import pytest

from src.models.schemas import Ingredient
from src.scripts.normalization.normalize_ingredients import normalize_ingredient


class TestNormalizeIngredient:
    def test_strips_parenthetical_qualifiers(self) -> None:
        result = normalize_ingredient("Gin (London Dry)")
        assert result == "Gin"

    def test_preserves_premium_liqueurs(self) -> None:
        result = normalize_ingredient("Crème de Cacao")
        assert result == "Crème De Cacao"

    def test_preserves_premium_liqueurs_kahlua(self) -> None:
        result = normalize_ingredient("Kahlúa")
        assert result == "Kahlúa"

    def test_normalizes_whitespace(self) -> None:
        result = normalize_ingredient("  Gin  ")
        assert result == "Gin"

    def test_normalizes_case(self) -> None:
        result = normalize_ingredient("gin")
        assert result == "Gin"

    def test_strips_inner_parens(self) -> None:
        result = normalize_ingredient("Gin (London Dry) (Distilled)")
        assert result == "Gin"

    def test_empty_string_returns_empty(self) -> None:
        result = normalize_ingredient("")
        assert result == ""

    def test_multiple_spaces(self) -> None:
        result = normalize_ingredient("Vodka   Lemon")
        assert result == "Vodka Lemon"

    def test_already_normalized(self) -> None:
        result = normalize_ingredient("Tequila")
        assert result == "Tequila"