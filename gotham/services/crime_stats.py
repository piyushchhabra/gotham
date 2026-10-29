"""Crime statistics for Commissioner Gordon's weekly briefing."""

from __future__ import annotations

from collections import Counter

from gotham.models.case import CaseStatus, Severity
from gotham.models.district import District
from gotham.services.gcpd import CaseService


class CrimeStats:
    def __init__(self, cases: CaseService) -> None:
        self._cases = cases

    def cases_by_district(self, active_only: bool = False) -> dict[District, int]:
        counts: Counter[District] = Counter()
        for case in self._cases.cases:
            if case.is_active or not active_only:
                counts[case.district] += 1
        return dict(counts)

    def severity_histogram(self) -> dict[Severity, int]:
        histogram = {severity: 0 for severity in Severity}
        for case in self._cases.cases:
            histogram[case.severity] += 1
        return histogram

    def hotspot(self) -> District | None:
        """District with the highest total severity of active cases; ties go alphabetically."""
        weight: Counter[District] = Counter()
        for case in self._cases.cases:
            if case.is_active:
                weight[case.district] += int(case.severity)
        if not weight:
            return None
        return min(weight, key=lambda d: (-weight[d], d.display_name))

    def clearance_rate(self) -> float:
        total = len(self._cases.cases)
        if total == 0:
            return 0.0
        solved = sum(1 for c in self._cases.cases if c.status is CaseStatus.SOLVED)
        return solved / total

    def average_days_to_solve(self) -> float | None:
        durations = [
            (c.closed_on - c.opened_on).days
            for c in self._cases.cases
            if c.status is CaseStatus.SOLVED and c.closed_on is not None
        ]
        if not durations:
            return None
        return sum(durations) / len(durations)
