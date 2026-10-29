from datetime import timedelta

import pytest

from gotham.exceptions import CapacityError, InvalidStateError, NotFoundError
from gotham.models.inmate import Wing
from gotham.models.villain import VillainStatus

from tests.conftest import TODAY

CUSTODY = VillainStatus.IN_CUSTODY


def test_admission_requires_custody(gotham, make_villain):
    make_villain("V1", "Scarecrow", 8)
    with pytest.raises(InvalidStateError):
        gotham.arkham.admit("V1", TODAY, 365)


@pytest.mark.parametrize("threat, wing", [(10, Wing.MAXIMUM), (6, Wing.HIGH), (3, Wing.MEDIUM)])
def test_wing_assigned_by_threat(gotham, make_villain, threat, wing):
    make_villain("V1", "Inmate", threat, status=CUSTODY)
    inmate = gotham.arkham.admit("V1", TODAY, 30)
    assert inmate.wing is wing
    assert inmate.cell == f"{wing.code}-01"
    assert gotham.villains.get("V1").status is VillainStatus.IN_ARKHAM


def test_cells_are_reused_lowest_first(gotham, make_villain):
    for i in range(1, 4):
        make_villain(f"V{i}", f"Goon {i}", 3, status=CUSTODY)
        gotham.arkham.admit(f"V{i}", TODAY, 30)
    gotham.arkham.record_escape("V2")
    make_villain("V9", "Goon 9", 3, status=CUSTODY)

    assert gotham.arkham.admit("V9", TODAY, 30).cell == "C-02"


def test_full_wing_rejects_admission(gotham, make_villain):
    for i in range(1, 4):
        make_villain(f"V{i}", f"Big Bad {i}", 9, status=CUSTODY)
        gotham.arkham.admit(f"V{i}", TODAY, 30)
    make_villain("V4", "The Joker", 10, status=CUSTODY)

    with pytest.raises(CapacityError):
        gotham.arkham.admit("V4", TODAY, 30)
    assert gotham.villains.get("V4").status is CUSTODY


def test_release_only_when_sentence_served(gotham, make_villain):
    make_villain("V1", "Catwoman", 4, status=CUSTODY)
    gotham.arkham.admit("V1", TODAY, 10)

    with pytest.raises(InvalidStateError):
        gotham.arkham.release("V1", TODAY + timedelta(days=9))
    villain = gotham.arkham.release("V1", TODAY + timedelta(days=10))

    assert villain.status is VillainStatus.REFORMED
    assert not gotham.arkham.is_inmate("V1")


def test_escape_puts_villain_back_at_large(gotham, make_villain):
    make_villain("V1", "The Joker", 10, status=CUSTODY)
    gotham.arkham.admit("V1", TODAY, 1000)

    gotham.arkham.record_escape("V1")

    assert gotham.villains.get("V1").status is VillainStatus.AT_LARGE
    assert gotham.arkham.escape_count("V1") == 1
    with pytest.raises(NotFoundError):
        gotham.arkham.inmate("V1")


def test_population_report_and_releases_due(gotham, make_villain):
    make_villain("V1", "Mr. Freeze", 7, status=CUSTODY)
    make_villain("V2", "Mad Hatter", 5, status=CUSTODY)
    make_villain("V3", "Ratcatcher", 2, status=CUSTODY)
    gotham.arkham.admit("V1", TODAY, 5)
    gotham.arkham.admit("V2", TODAY, 50)
    gotham.arkham.admit("V3", TODAY, 1)

    assert gotham.arkham.population_report() == {"A": (0, 3), "B": (2, 5), "C": (1, 10)}
    assert gotham.arkham.due_for_release(TODAY + timedelta(days=5)) == ["V1", "V3"]
