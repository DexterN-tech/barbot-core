"""Pydantic models for recipe ingestion."""

from typing import Literal

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    schema_version: str = "1.0.0"
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    alcoholic: bool
    unit: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=0)
    aliases: list[str] = Field(default_factory=list)


class Ingredient(BaseModel):
    inventory_id: str = Field(..., min_length=1)
    amount_shots: float = Field(..., gt=0)


class Recipe(BaseModel):
    schema_version: str = "1.0.0"
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    iba_verified: bool = False
    ingredients: list[Ingredient] = Field(default_factory=list)
    garnish: list[str] = Field(default_factory=list)
    glassware: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class InstructionStep(BaseModel):
    step: int = Field(..., ge=1)
    station: Literal[
        "fluid_dispenser",
        "ice_dispenser",
        "shaker_module",
        "stir_module",
        "user_prompt",
    ]
    action: str = Field(..., min_length=1)
    payload: dict = Field(default_factory=dict)


class InstructionSet(BaseModel):
    schema_version: str = "1.0.0"
    recipe_id: str = Field(..., min_length=1)
    steps: list[InstructionStep] = Field(default_factory=list)