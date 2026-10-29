from __future__ import annotations

from dataclasses import dataclass, field

from gotham.models.district import District


@dataclass
class Ally:
    ally_id: str
    codename: str
    location: District
    skills: set[str] = field(default_factory=set)
    available: bool = True

    def move_to(self, district: District) -> None:
        self.location = district

    def has_skill(self, skill: str) -> bool:
        return skill in self.skills
