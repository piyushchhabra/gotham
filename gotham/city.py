"""Wires every repository and service together."""

from __future__ import annotations

from decimal import Decimal

from gotham.models.ally import Ally
from gotham.models.villain import Villain
from gotham.repository import InMemoryRepository
from gotham.services.arkham import ArkhamAsylum
from gotham.services.batcave import GadgetInventory, UtilityBelt
from gotham.services.crime_stats import CrimeStats
from gotham.services.dispatch import BatSignal
from gotham.services.finance import WayneFinance
from gotham.services.gcpd import CaseService
from gotham.services.patrol import CityMap
from gotham.services.threat import ThreatAssessor

DEFAULT_BUDGETS = {
    "Applied Sciences": Decimal("2500000.00"),
    "Vehicles": Decimal("4000000.00"),
    "Wayne Foundation": Decimal("1000000.00"),
}


class Gotham:
    def __init__(self, budgets: dict[str, Decimal] | None = None) -> None:
        self.villains: InMemoryRepository[str, Villain] = InMemoryRepository("Villain", lambda v: v.villain_id)
        self.allies: InMemoryRepository[str, Ally] = InMemoryRepository("Ally", lambda a: a.ally_id)
        self.city_map = CityMap()
        self.inventory = GadgetInventory()
        self.gcpd = CaseService(self.villains)
        self.arkham = ArkhamAsylum(self.villains)
        self.threats = ThreatAssessor(self.arkham, self.gcpd)
        self.bat_signal = BatSignal(self.allies, self.city_map)
        self.finance = WayneFinance(budgets if budgets is not None else DEFAULT_BUDGETS)
        self.stats = CrimeStats(self.gcpd)

    def new_utility_belt(self, **kwargs) -> UtilityBelt:
        return UtilityBelt(self.inventory, **kwargs)
