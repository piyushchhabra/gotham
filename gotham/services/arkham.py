"""Arkham Asylum intake, cell allocation, releases and escapes."""

from __future__ import annotations

from collections import Counter
from datetime import date

from gotham.exceptions import CapacityError, InvalidStateError, NotFoundError
from gotham.models.inmate import Inmate, Wing
from gotham.models.villain import Villain, VillainStatus
from gotham.repository import InMemoryRepository


class ArkhamAsylum:
    def __init__(self, villains: InMemoryRepository[str, Villain]) -> None:
        self._villains = villains
        self._inmates: dict[str, Inmate] = {}
        self._escapes: Counter[str] = Counter()

    def admit(self, villain_id: str, admitted_on: date, sentence_days: int) -> Inmate:
        villain = self._villains.get(villain_id)
        if villain.status is not VillainStatus.IN_CUSTODY:
            raise InvalidStateError(f"{villain.alias} must be in GCPD custody to be admitted")
        if sentence_days <= 0:
            raise ValueError("Sentence must be at least one day")

        wing = Wing.for_threat(villain.threat_level)
        cell = self._free_cell(wing)
        inmate = Inmate(villain_id, wing, cell, admitted_on, sentence_days)
        self._inmates[villain_id] = inmate
        villain.status = VillainStatus.IN_ARKHAM
        return inmate

    def release(self, villain_id: str, today: date) -> Villain:
        inmate = self.inmate(villain_id)
        if not inmate.is_eligible_for_release(today):
            raise InvalidStateError(
                f"{villain_id} is not eligible for release until {inmate.release_date.isoformat()}"
            )
        del self._inmates[villain_id]
        villain = self._villains.get(villain_id)
        villain.status = VillainStatus.REFORMED
        return villain

    def record_escape(self, villain_id: str) -> Villain:
        self.inmate(villain_id)
        del self._inmates[villain_id]
        self._escapes[villain_id] += 1
        villain = self._villains.get(villain_id)
        villain.status = VillainStatus.AT_LARGE
        return villain

    def inmate(self, villain_id: str) -> Inmate:
        try:
            return self._inmates[villain_id]
        except KeyError:
            raise NotFoundError("Inmate", villain_id) from None

    def is_inmate(self, villain_id: str) -> bool:
        return villain_id in self._inmates

    def escape_count(self, villain_id: str) -> int:
        return self._escapes[villain_id]

    def occupants(self, wing: Wing) -> list[Inmate]:
        return sorted((i for i in self._inmates.values() if i.wing is wing), key=lambda i: i.cell)

    def occupancy(self, wing: Wing) -> int:
        return len(self.occupants(wing))

    def population_report(self) -> dict[str, tuple[int, int]]:
        return {wing.code: (self.occupancy(wing), wing.capacity) for wing in Wing}

    def due_for_release(self, today: date) -> list[str]:
        return sorted(v for v, i in self._inmates.items() if i.is_eligible_for_release(today))

    def _free_cell(self, wing: Wing) -> str:
        taken = {i.cell for i in self._inmates.values() if i.wing is wing}
        for number in range(1, wing.capacity + 1):
            cell = f"{wing.code}-{number:02d}"
            if cell not in taken:
                return cell
        raise CapacityError(f"Arkham wing {wing.code} is full")
