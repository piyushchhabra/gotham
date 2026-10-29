"""GCPD case management."""

from __future__ import annotations

from datetime import date
from itertools import count

from gotham.exceptions import InvalidStateError
from gotham.models.case import Case, CaseStatus, Severity
from gotham.models.district import District
from gotham.models.villain import Villain, VillainStatus
from gotham.repository import InMemoryRepository


class CaseService:
    COLD_AFTER_DAYS = 90

    def __init__(self, villains: InMemoryRepository[str, Villain]) -> None:
        self._villains = villains
        self.cases: InMemoryRepository[str, Case] = InMemoryRepository("Case", lambda c: c.case_id)
        self._sequence = count(1)

    def open_case(self, title: str, district: District, severity: Severity, opened_on: date) -> Case:
        case = Case(f"GCPD-{next(self._sequence):04d}", title, district, severity, opened_on)
        return self.cases.save(case)

    def assign(self, case_id: str, detective: str) -> Case:
        case = self._active_case(case_id)
        case.detective = detective
        case.status = CaseStatus.ASSIGNED
        return case

    def add_suspect(self, case_id: str, villain_id: str) -> Case:
        case = self._active_case(case_id)
        self._villains.get(villain_id)
        if villain_id not in case.suspects:
            case.suspects.append(villain_id)
        return case

    def add_note(self, case_id: str, note: str) -> Case:
        case = self.cases.get(case_id)
        case.notes.append(note)
        return case

    def solve(self, case_id: str, closed_on: date, culprit_id: str | None = None) -> Case:
        case = self._active_case(case_id)
        if closed_on < case.opened_on:
            raise ValueError("A case cannot be closed before it was opened")
        if culprit_id is not None:
            if culprit_id not in case.suspects:
                raise InvalidStateError(f"{culprit_id} is not a suspect in {case_id}")
            culprit = self._villains.get(culprit_id)
            if culprit.status is VillainStatus.AT_LARGE:
                culprit.apprehend()
        case.status = CaseStatus.SOLVED
        case.closed_on = closed_on
        return case

    def sweep_cold_cases(self, today: date) -> list[Case]:
        """Unassigned cases open for COLD_AFTER_DAYS or more go cold."""
        gone_cold = []
        for case in self.cases:
            if case.status is CaseStatus.OPEN and case.age_in_days(today) >= self.COLD_AFTER_DAYS:
                case.status = CaseStatus.COLD
                gone_cold.append(case)
        return gone_cold

    def active_cases(self) -> list[Case]:
        """Most severe first; equally severe cases oldest first."""
        active = self.cases.filter(lambda c: c.is_active)
        return sorted(active, key=lambda c: (-c.severity, c.opened_on, c.case_id))

    def cases_for_villain(self, villain_id: str, active_only: bool = True) -> list[Case]:
        return self.cases.filter(
            lambda c: villain_id in c.suspects and (c.is_active or not active_only)
        )

    def caseload(self) -> dict[str, int]:
        load: dict[str, int] = {}
        for case in self.cases:
            if case.status is CaseStatus.ASSIGNED and case.detective:
                load[case.detective] = load.get(case.detective, 0) + 1
        return dict(sorted(load.items()))

    def dossier(self, villain_id: str) -> dict:
        villain = self._villains.get(villain_id)
        return {
            "alias": villain.alias,
            "real_name": villain.real_name,
            "status": villain.status.value,
            "threat_level": villain.threat_level,
            "known_associates": sorted(villain.known_associates),
            "open_cases": [c.case_id for c in self.cases_for_villain(villain_id)],
        }

    def _active_case(self, case_id: str) -> Case:
        case = self.cases.get(case_id)
        if not case.is_active:
            raise InvalidStateError(f"{case_id} is {case.status.value}")
        return case
