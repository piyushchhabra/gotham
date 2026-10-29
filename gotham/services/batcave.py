"""Batcave armoury: gadget stock and utility-belt loadouts."""

from __future__ import annotations

from collections import Counter

from gotham.exceptions import CapacityError, InvalidStateError, NotFoundError
from gotham.models.gadget import Gadget, GadgetCategory


class GadgetInventory:
    def __init__(self) -> None:
        self._catalog: dict[str, Gadget] = {}
        self._stock: Counter[str] = Counter()

    def register(self, gadget: Gadget, quantity: int = 0) -> None:
        if gadget.name in self._catalog:
            raise InvalidStateError(f"{gadget.name} is already in the catalog")
        self._catalog[gadget.name] = gadget
        if quantity:
            self.restock(gadget.name, quantity)

    def gadget(self, name: str) -> Gadget:
        try:
            return self._catalog[name]
        except KeyError:
            raise NotFoundError("Gadget", name) from None

    def restock(self, name: str, quantity: int) -> None:
        self.gadget(name)
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")
        self._stock[name] += quantity

    def stock_of(self, name: str) -> int:
        self.gadget(name)
        return self._stock[name]

    def take(self, name: str, quantity: int = 1) -> Gadget:
        gadget = self.gadget(name)
        if self._stock[name] < quantity:
            raise InvalidStateError(f"Only {self._stock[name]} x {name} left in the Batcave")
        self._stock[name] -= quantity
        return gadget

    def put_back(self, name: str, quantity: int = 1) -> None:
        self.gadget(name)
        self._stock[name] += quantity

    def low_stock(self, threshold: int = 2) -> list[str]:
        return sorted(name for name in self._catalog if self._stock[name] <= threshold)

    def by_category(self, category: GadgetCategory) -> list[Gadget]:
        return [g for g in self._catalog.values() if g.category is category]


class UtilityBelt:
    """A belt has a fixed number of pouches and a maximum carry weight (inclusive)."""

    DEFAULT_MAX_WEIGHT_GRAMS = 2000
    DEFAULT_SLOTS = 8

    def __init__(
        self,
        inventory: GadgetInventory,
        max_weight_grams: int = DEFAULT_MAX_WEIGHT_GRAMS,
        slots: int = DEFAULT_SLOTS,
    ) -> None:
        self._inventory = inventory
        self.max_weight_grams = max_weight_grams
        self.slots = slots
        self._gadgets: list[Gadget] = []

    @property
    def gadgets(self) -> list[Gadget]:
        return list(self._gadgets)

    @property
    def total_weight(self) -> int:
        return sum(g.weight_grams for g in self._gadgets)

    @property
    def remaining_weight(self) -> int:
        return self.max_weight_grams - self.total_weight

    @property
    def free_slots(self) -> int:
        return self.slots - len(self._gadgets)

    def can_carry(self, gadget: Gadget) -> bool:
        if self.free_slots <= 0:
            return False
        return self.total_weight + gadget.weight_grams < self.max_weight_grams

    def equip(self, name: str) -> Gadget:
        gadget = self._inventory.gadget(name)
        if not self.can_carry(gadget):
            raise CapacityError(f"No room on the belt for {name}")
        self._inventory.take(name)
        self._gadgets.append(gadget)
        return gadget

    def unequip(self, name: str) -> Gadget:
        for i, gadget in enumerate(self._gadgets):
            if gadget.name == name:
                del self._gadgets[i]
                self._inventory.put_back(name)
                return gadget
        raise NotFoundError("Gadget on belt", name)

    def count(self, name: str) -> int:
        return sum(1 for g in self._gadgets if g.name == name)

    def categories(self) -> set[GadgetCategory]:
        return {g.category for g in self._gadgets}

    def empty(self) -> None:
        for gadget in list(self._gadgets):
            self.unequip(gadget.name)

    def auto_loadout(self, wishlist: list[str]) -> list[str]:
        """Equip items from the wishlist in order, skipping anything that doesn't fit or is out of stock."""
        equipped = []
        for name in wishlist:
            gadget = self._inventory.gadget(name)
            if self._inventory.stock_of(name) == 0 or not self.can_carry(gadget):
                continue
            self.equip(name)
            equipped.append(name)
        return equipped
