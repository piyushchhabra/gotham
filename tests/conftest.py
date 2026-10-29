from __future__ import annotations

from datetime import date

import pytest

from gotham.city import Gotham
from gotham.models.ally import Ally
from gotham.models.district import District
from gotham.models.villain import Villain, VillainStatus

TODAY = date(2026, 10, 29)


@pytest.fixture
def gotham() -> Gotham:
    return Gotham()


@pytest.fixture
def make_villain(gotham):
    def factory(
        villain_id: str,
        alias: str,
        threat_level: int = 5,
        status: VillainStatus = VillainStatus.AT_LARGE,
        associates: tuple[str, ...] = (),
        real_name: str | None = None,
    ) -> Villain:
        villain = Villain(villain_id, alias, real_name, threat_level, status, list(associates))
        return gotham.villains.save(villain)

    return factory


@pytest.fixture
def make_ally(gotham):
    def factory(ally_id: str, codename: str, location: District, *skills: str) -> Ally:
        return gotham.allies.save(Ally(ally_id, codename, location, set(skills)))

    return factory
