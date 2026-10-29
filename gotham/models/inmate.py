from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


class Wing(Enum):
    """Arkham wings, from most to least secure."""

    MAXIMUM = ("A", 8, 3)
    HIGH = ("B", 5, 5)
    MEDIUM = ("C", 1, 10)

    def __init__(self, code: str, min_threat: int, capacity: int) -> None:
        self.code = code
        self.min_threat = min_threat
        self.capacity = capacity

    @classmethod
    def for_threat(cls, threat_level: int) -> "Wing":
        for wing in cls:
            if threat_level >= wing.min_threat:
                return wing
        return cls.MEDIUM


@dataclass
class Inmate:
    villain_id: str
    wing: Wing
    cell: str
    admitted_on: date
    sentence_days: int

    @property
    def release_date(self) -> date:
        return self.admitted_on + timedelta(days=self.sentence_days)

    def days_served(self, today: date) -> int:
        return max(0, (today - self.admitted_on).days)

    def is_eligible_for_release(self, today: date) -> bool:
        return today >= self.release_date
