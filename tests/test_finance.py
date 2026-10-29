from datetime import date
from decimal import Decimal

import pytest

from gotham.exceptions import CapacityError, NotFoundError
from gotham.models.gadget import Gadget, GadgetCategory
from gotham.services.batcave import GadgetInventory
from gotham.services.finance import WayneFinance, to_money


@pytest.fixture
def finance() -> WayneFinance:
    return WayneFinance({"Applied Sciences": "10000", "Vehicles": "50000.50"})


@pytest.fixture
def inventory() -> GadgetInventory:
    inv = GadgetInventory()
    inv.register(Gadget("Batarang", 120, GadgetCategory.THROWABLE, Decimal("85.00")))
    inv.register(Gadget("Smoke Pellet", 60, GadgetCategory.THROWABLE, Decimal("12.345")))
    return inv


def test_to_money_rounds_half_up():
    assert to_money("2.675") == Decimal("2.68")
    assert to_money("2.665") == Decimal("2.67")
    assert to_money(5) == Decimal("5.00")


def test_spend_reduces_remaining(finance):
    finance.spend("Vehicles", "12000.25", "Batmobile tyres", date(2026, 2, 1))
    assert finance.remaining("Vehicles") == Decimal("38000.25")
    assert finance.spent("Vehicles") == Decimal("12000.25")


def test_cannot_overspend(finance):
    with pytest.raises(CapacityError):
        finance.spend("Applied Sciences", "10000.01", "Too much", date(2026, 2, 1))
    finance.spend("Applied Sciences", "10000.00", "Everything", date(2026, 2, 1))
    assert finance.remaining("Applied Sciences") == Decimal("0.00")


def test_unknown_division(finance):
    with pytest.raises(NotFoundError):
        finance.remaining("Wayne Casinos")


def test_quote_applies_bulk_discount(finance, inventory):
    batarang = inventory.gadget("Batarang")
    assert finance.quote(batarang, 9) == Decimal("765.00")
    assert finance.quote(batarang, 10) == Decimal("765.00")
    assert finance.quote(batarang, 20) == Decimal("1530.00")


def test_quote_rounds_to_cents(finance, inventory):
    assert finance.quote(inventory.gadget("Smoke Pellet"), 3) == Decimal("37.04")


def test_purchase_restocks_inventory(finance, inventory):
    transaction = finance.purchase_gadgets(inventory, "Batarang", 10, date(2026, 3, 15))
    assert transaction.amount == Decimal("765.00")
    assert inventory.stock_of("Batarang") == 10
    assert finance.remaining("Applied Sciences") == Decimal("9235.00")


def test_failed_purchase_does_not_restock(finance, inventory):
    with pytest.raises(CapacityError):
        finance.purchase_gadgets(inventory, "Batarang", 200, date(2026, 3, 15))
    assert inventory.stock_of("Batarang") == 0


def test_quarterly_report(finance):
    finance.spend("Vehicles", "100", "Q1", date(2026, 3, 31))
    finance.spend("Vehicles", "200", "Q2", date(2026, 4, 1))
    finance.spend("Applied Sciences", "50", "Q2", date(2026, 6, 30))

    assert finance.quarterly_report(2026, 2) == {
        "Applied Sciences": Decimal("50.00"),
        "Vehicles": Decimal("200.00"),
    }
    with pytest.raises(ValueError):
        finance.quarterly_report(2026, 5)
