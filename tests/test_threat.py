from datetime import date

from gotham.models.case import Severity
from gotham.models.district import District
from gotham.models.villain import Villain, VillainStatus
from gotham.services.threat import ThreatAssessor, ThreatLevel

from tests.conftest import TODAY


def test_score_formula(gotham, make_villain):
    riddler = make_villain("V1", "The Riddler", 7, associates=("Query", "Echo"))
    assert gotham.threats.score(riddler) == 70 + 10 + 15


def test_no_at_large_bonus_when_locked_up(gotham, make_villain):
    freeze = make_villain("V1", "Mr. Freeze", 7, status=VillainStatus.IN_ARKHAM)
    assert gotham.threats.score(freeze) == 70


def test_escapes_raise_the_score(gotham, make_villain):
    ivy = make_villain("V1", "Poison Ivy", 6, status=VillainStatus.IN_CUSTODY)
    gotham.arkham.admit("V1", TODAY, 100)
    gotham.arkham.record_escape("V1")
    assert gotham.threats.score(ivy) == 60 + 15 + 8


def test_open_cases_raise_the_score(gotham, make_villain):
    penguin = make_villain("V1", "The Penguin", 6)
    case = gotham.gcpd.open_case("Iceberg Lounge smuggling", District.EAST_END, Severity.SERIOUS, TODAY)
    gotham.gcpd.add_suspect(case.case_id, "V1")
    assert gotham.threats.score(penguin) == 60 + 15 + 3

    gotham.gcpd.solve(case.case_id, TODAY)
    assert gotham.threats.score(penguin) == 60 + 15


def test_standalone_assessor_ignores_arkham_and_gcpd(make_villain):
    joker = make_villain("V1", "The Joker", 10, associates=("Harley Quinn",))
    assert ThreatAssessor().score(joker) == 100 + 5 + 15


def test_classification_thresholds(gotham, make_villain):
    assert gotham.threats.classify(make_villain("V1", "Ratcatcher", 2)) is ThreatLevel.LOW
    assert gotham.threats.classify(make_villain("V2", "Mad Hatter", 4)) is ThreatLevel.ELEVATED
    assert gotham.threats.classify(make_villain("V3", "Bane", 9)) is ThreatLevel.HIGH
    assert gotham.threats.classify(make_villain("V4", "The Joker", 10, associates=("Harley Quinn",))) is ThreatLevel.CRITICAL


def test_rank_orders_by_score_then_alias(gotham, make_villain):
    two_face = make_villain("V1", "Two-Face", 7)
    riddler = make_villain("V2", "The Riddler", 7)
    joker = make_villain("V3", "The Joker", 10)

    ranked = gotham.threats.rank([two_face, riddler, joker])

    assert [v.alias for v, _ in ranked] == ["The Joker", "The Riddler", "Two-Face"]


def test_most_wanted_only_includes_villains_at_large(gotham, make_villain):
    make_villain("V1", "The Joker", 10, status=VillainStatus.IN_ARKHAM)
    make_villain("V2", "Scarecrow", 8)
    make_villain("V3", "Catwoman", 4)
    make_villain("V4", "Killer Croc", 6)

    wanted = gotham.threats.most_wanted(gotham.villains.all(), limit=2)

    assert [v.alias for v in wanted] == ["Scarecrow", "Killer Croc"]


def test_recruiting_henchmen_does_not_change_other_villains_scores(gotham):
    joker = gotham.villains.save(Villain("V1", "The Joker", threat_level=10))
    penguin = gotham.villains.save(Villain("V2", "The Penguin", "Oswald Cobblepot", 6))
    penguin_before = gotham.threats.score(penguin)

    joker.add_associate("Harley Quinn")
    joker.add_associate("Frost")

    assert gotham.threats.score(penguin) == penguin_before
