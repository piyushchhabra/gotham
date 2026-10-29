from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class GadgetCategory(Enum):
    THROWABLE = "throwable"
    GRAPPLE = "grapple"
    MEDICAL = "medical"
    FORENSIC = "forensic"
    EXPLOSIVE = "explosive"
    COMMUNICATION = "communication"


@dataclass(frozen=True)
class Gadget:
    name: str
    weight_grams: int
    category: GadgetCategory
    unit_cost: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Gadget name is required")
        if self.weight_grams <= 0:
            raise ValueError("Gadget weight must be positive")
        if self.unit_cost < 0:
            raise ValueError("Gadget cost cannot be negative")
