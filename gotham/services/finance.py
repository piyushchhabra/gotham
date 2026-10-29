"""Wayne Enterprises off-the-books budgets that fund the Batcave."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from gotham.exceptions import CapacityError, NotFoundError
from gotham.models.gadget import Gadget
from gotham.services.batcave import GadgetInventory

CENT = Decimal("0.01")


def to_money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    division: str
    amount: Decimal
    description: str
    on: date

    @property
    def quarter(self) -> tuple[int, int]:
        return self.on.year, (self.on.month - 1) // 3 + 1


class WayneFinance:
    BULK_THRESHOLD = 10
    BULK_DISCOUNT = Decimal("0.10")

    def __init__(self, budgets: dict[str, Decimal | int | str]) -> None:
        self._budgets = {division: to_money(amount) for division, amount in budgets.items()}
        self._ledger: list[Transaction] = []

    def divisions(self) -> list[str]:
        return sorted(self._budgets)

    def budget(self, division: str) -> Decimal:
        try:
            return self._budgets[division]
        except KeyError:
            raise NotFoundError("Division", division) from None

    def spent(self, division: str) -> Decimal:
        self.budget(division)
        return sum((t.amount for t in self._ledger if t.division == division), Decimal("0.00"))

    def remaining(self, division: str) -> Decimal:
        return self.budget(division) - self.spent(division)

    def spend(self, division: str, amount: Decimal | int | str, description: str, on: date) -> Transaction:
        amount = to_money(amount)
        if amount <= 0:
            raise ValueError("Spend amount must be positive")
        if amount > self.remaining(division):
            raise CapacityError(
                f"{division} cannot cover {amount}; only {self.remaining(division)} remaining"
            )
        transaction = Transaction(division, amount, description, on)
        self._ledger.append(transaction)
        return transaction

    def quote(self, gadget: Gadget, quantity: int) -> Decimal:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        total = gadget.unit_cost * quantity
        if quantity >= self.BULK_THRESHOLD:
            total = total * (1 - self.BULK_DISCOUNT)
        return to_money(total)

    def purchase_gadgets(
        self,
        inventory: GadgetInventory,
        gadget_name: str,
        quantity: int,
        on: date,
        division: str = "Applied Sciences",
    ) -> Transaction:
        gadget = inventory.gadget(gadget_name)
        transaction = self.spend(division, self.quote(gadget, quantity), f"{quantity} x {gadget_name}", on)
        inventory.restock(gadget_name, quantity)
        return transaction

    def ledger(self, division: str | None = None) -> list[Transaction]:
        return [t for t in self._ledger if division is None or t.division == division]

    def quarterly_report(self, year: int, quarter: int) -> dict[str, Decimal]:
        if quarter not in (1, 2, 3, 4):
            raise ValueError("Quarter must be 1-4")
        report = {division: Decimal("0.00") for division in self.divisions()}
        for t in self._ledger:
            if t.quarter == (year, quarter):
                report[t.division] += t.amount
        return report
