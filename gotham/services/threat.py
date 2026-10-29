"""Threat assessment for Gotham's rogues gallery."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Iterable

from gotham.models.villain import Villain, VillainStatus

if TYPE_CHECKING:
    from gotham.services.arkham import ArkhamAsylum
    from gotham.services.gcpd import CaseService


class ThreatLevel(Enum):
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatAssessor:
    """
    score = 10 x threat level
          + 5 per known associate
          + 15 if at large
          + 8 per escape from Arkham
          + 3 per open GCPD case naming them as a suspect
    """

    THREAT_WEIGHT = 10
    ASSOCIATE_WEIGHT = 5
    AT_LARGE_BONUS = 15
    ESCAPE_WEIGHT = 8
    OPEN_CASE_WEIGHT = 3

    THRESHOLDS = (
        (110, ThreatLevel.CRITICAL),
        (80, ThreatLevel.HIGH),
        (50, ThreatLevel.ELEVATED),
    )

    def __init__(self, arkham: ArkhamAsylum | None = None, cases: CaseService | None = None) -> None:
        self._arkham = arkham
        self._cases = cases

    def score(self, villain: Villain) -> int:
        total = villain.threat_level * self.THREAT_WEIGHT
        total += len(villain.known_associates) * self.ASSOCIATE_WEIGHT
        if villain.status is VillainStatus.AT_LARGE:
            total += self.AT_LARGE_BONUS
        if self._arkham is not None:
            total += self._arkham.escape_count(villain.villain_id) * self.ESCAPE_WEIGHT
        if self._cases is not None:
            total += len(self._cases.cases_for_villain(villain.villain_id)) * self.OPEN_CASE_WEIGHT
        return total

    def classify(self, villain: Villain) -> ThreatLevel:
        score = self.score(villain)
        for threshold, level in self.THRESHOLDS:
            if score >= threshold:
                return level
        return ThreatLevel.LOW

    def rank(self, villains: Iterable[Villain]) -> list[tuple[Villain, int]]:
        scored = [(v, self.score(v)) for v in villains]
        return sorted(scored, key=lambda pair: (-pair[1], pair[0].alias))

    def most_wanted(self, villains: Iterable[Villain], limit: int = 3) -> list[Villain]:
        at_large = [v for v in villains if v.is_at_large]
        return [v for v, _ in self.rank(at_large)[:limit]]
