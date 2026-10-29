from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum, IntEnum

from gotham.models.district import District


class Severity(IntEnum):
    MINOR = 1
    MODERATE = 2
    SERIOUS = 3
    MAJOR = 4
    CITYWIDE = 5


class CaseStatus(Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    SOLVED = "solved"
    COLD = "cold"


@dataclass
class Case:
    case_id: str
    title: str
    district: District
    severity: Severity
    opened_on: date
    status: CaseStatus = CaseStatus.OPEN
    detective: str | None = None
    suspects: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    closed_on: date | None = None

    @property
    def is_active(self) -> bool:
        return self.status in (CaseStatus.OPEN, CaseStatus.ASSIGNED)

    def age_in_days(self, today: date) -> int:
        end = self.closed_on or today
        return (end - self.opened_on).days
