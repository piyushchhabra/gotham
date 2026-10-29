from decimal import Decimal

import pytest

from gotham.exceptions import CapacityError, InvalidStateError, NotFoundError
from gotham.models.gadget import Gadget, GadgetCategory
from gotham.services.batcave import GadgetInventory, UtilityBelt


@pytest.fixture
def inventory() -> GadgetInventory:
    inv = GadgetInventory()
    inv.register(Gadget("Batarang", 120, GadgetCategory.THROWABLE, Decimal("85")), 10)
    inv.register(Gadget("Grapnel Gun", 900, GadgetCategory.GRAPPLE, Decimal("12500")), 2)
    inv.register(Gadget("Smoke Pellet", 60, GadgetCategory.THROWABLE, Decimal("12.50")), 5)
    inv.register(Gadget("Explosive Gel", 300, GadgetCategory.EXPLOSIVE, Decimal("640")), 1)
    inv.register(Gadget("Rebreather", 200, GadgetCategory.MEDICAL, Decimal("980")), 0)
    return inv


class TestInventory:
    def test_take_reduces_stock(self, inventory):
        inventory.take("Batarang", 3)
        assert inventory.stock_of("Batarang") == 7

    def test_cannot_take_more_than_stock(self, inventory):
        with pytest.raises(InvalidStateError):
            inventory.take("Grapnel Gun", 3)
        assert inventory.stock_of("Grapnel Gun") == 2

    def test_unknown_gadget(self, inventory):
        with pytest.raises(NotFoundError):
            inventory.stock_of("Shark Repellent")

    def test_duplicate_registration_rejected(self, inventory):
        with pytest.raises(InvalidStateError):
            inventory.register(Gadget("Batarang", 100, GadgetCategory.THROWABLE))

    def test_low_stock_report(self, inventory):
        assert inventory.low_stock(threshold=2) == ["Explosive Gel", "Grapnel Gun", "Rebreather"]

    def test_by_category(self, inventory):
        names = [g.name for g in inventory.by_category(GadgetCategory.THROWABLE)]
        assert names == ["Batarang", "Smoke Pellet"]


class TestUtilityBelt:
    def test_equip_takes_from_inventory(self, inventory):
        belt = UtilityBelt(inventory)
        belt.equip("Batarang")
        belt.equip("Batarang")
        assert belt.count("Batarang") == 2
        assert belt.total_weight == 240
        assert inventory.stock_of("Batarang") == 8

    def test_unequip_returns_to_inventory(self, inventory):
        belt = UtilityBelt(inventory)
        belt.equip("Grapnel Gun")
        belt.unequip("Grapnel Gun")
        assert belt.gadgets == []
        assert inventory.stock_of("Grapnel Gun") == 2

    def test_unequip_missing_gadget(self, inventory):
        with pytest.raises(NotFoundError):
            UtilityBelt(inventory).unequip("Batarang")

    def test_rejects_gadget_over_weight_limit(self, inventory):
        belt = UtilityBelt(inventory, max_weight_grams=1000)
        belt.equip("Grapnel Gun")
        with pytest.raises(CapacityError):
            belt.equip("Batarang")
        assert inventory.stock_of("Batarang") == 10

    def test_belt_can_be_loaded_to_exactly_its_weight_limit(self, inventory):
        belt = UtilityBelt(inventory, max_weight_grams=1020)
        belt.equip("Grapnel Gun")
        belt.equip("Batarang")
        assert belt.total_weight == 1020
        assert belt.remaining_weight == 0

    def test_rejects_gadget_when_out_of_slots(self, inventory):
        belt = UtilityBelt(inventory, slots=2)
        belt.equip("Smoke Pellet")
        belt.equip("Smoke Pellet")
        with pytest.raises(CapacityError):
            belt.equip("Smoke Pellet")
        assert belt.free_slots == 0

    def test_out_of_stock_gadget_cannot_be_equipped(self, inventory):
        with pytest.raises(InvalidStateError):
            UtilityBelt(inventory).equip("Rebreather")

    def test_auto_loadout_skips_what_does_not_fit(self, inventory):
        belt = UtilityBelt(inventory, max_weight_grams=1000)
        equipped = belt.auto_loadout(["Grapnel Gun", "Explosive Gel", "Rebreather", "Smoke Pellet"])
        assert equipped == ["Grapnel Gun", "Smoke Pellet"]
        assert belt.categories() == {GadgetCategory.GRAPPLE, GadgetCategory.THROWABLE}

    def test_empty_returns_everything(self, inventory):
        belt = UtilityBelt(inventory)
        belt.auto_loadout(["Batarang", "Batarang", "Explosive Gel"])
        belt.empty()
        assert belt.gadgets == []
        assert inventory.stock_of("Batarang") == 10
        assert inventory.stock_of("Explosive Gel") == 1
