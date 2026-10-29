from __future__ import annotations

from enum import Enum


class VillainStatus(Enum):
    AT_LARGE = "at large"
    IN_CUSTODY = "in GCPD custody"
    IN_ARKHAM = "in Arkham"
    REFORMED = "reformed"


class Villain:
    MIN_THREAT = 1
    MAX_THREAT = 10

    def __init__(
        self,
        villain_id: str,
        alias: str,
        real_name: str | None = None,
        threat_level: int = 5,
        status: VillainStatus = VillainStatus.AT_LARGE,
        known_associates: list[str] = [],
    ) -> None:
        if not villain_id:
            raise ValueError("villain_id is required")
        if not alias:
            raise ValueError("alias is required")
        if not self.MIN_THREAT <= threat_level <= self.MAX_THREAT:
            raise ValueError(f"threat_level must be between {self.MIN_THREAT} and {self.MAX_THREAT}")
        self.villain_id = villain_id
        self.alias = alias
        self.real_name = real_name
        self.threat_level = threat_level
        self.status = status
        self.known_associates = known_associates

    def add_associate(self, name: str) -> None:
        if name and name not in self.known_associates:
            self.known_associates.append(name)

    def remove_associate(self, name: str) -> None:
        if name in self.known_associates:
            self.known_associates.remove(name)

    @property
    def is_at_large(self) -> bool:
        return self.status is VillainStatus.AT_LARGE

    def apprehend(self) -> None:
        if self.status is not VillainStatus.AT_LARGE:
            raise ValueError(f"{self.alias} is not at large ({self.status.value})")
        self.status = VillainStatus.IN_CUSTODY

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Villain) and other.villain_id == self.villain_id

    def __hash__(self) -> int:
        return hash(self.villain_id)

    def __repr__(self) -> str:
        return f"Villain({self.villain_id!r}, {self.alias!r}, threat={self.threat_level}, {self.status.name})"
