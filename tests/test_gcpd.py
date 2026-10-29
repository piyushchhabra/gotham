from datetime import timedelta

import pytest

from gotham.exceptions import InvalidStateError, NotFoundError
from gotham.models.case import CaseStatus, Severity
from gotham.models.district import District
from gotham.models.villain import Villain, VillainStatus

from tests.conftest import TODAY


def test_case_ids_are_sequential(gotham):
    a = gotham.gcpd.open_case("a", District.EAST_END, Severity.MINOR, TODAY)
    b = gotham.gcpd.open_case("b", District.EAST_END, Severity.MINOR, TODAY)
    assert (a.case_id, b.case_id) == ("GCPD-0001", "GCPD-0002")
    assert a.status is CaseStatus.OPEN


def test_assign_detective(gotham):
    case = gotham.gcpd.open_case("Bank job", District.DIAMOND_DISTRICT, Severity.SERIOUS, TODAY)
    gotham.gcpd.assign(case.case_id, "Det. Harvey Bullock")
    assert case.status is CaseStatus.ASSIGNED
    assert case.detective == "Det. Harvey Bullock"


def test_closed_cases_cannot_be_reassigned(gotham):
    case = gotham.gcpd.open_case("Bank job", District.DIAMOND_DISTRICT, Severity.SERIOUS, TODAY)
    gotham.gcpd.solve(case.case_id, TODAY)
    with pytest.raises(InvalidStateError):
        gotham.gcpd.assign(case.case_id, "Det. Harvey Bullock")


def test_suspects_must_exist_and_are_not_duplicated(gotham, make_villain):
    make_villain("V1", "Two-Face", 7)
    case = gotham.gcpd.open_case("Coin-toss robberies", District.OLD_GOTHAM, Severity.MAJOR, TODAY)
    gotham.gcpd.add_suspect(case.case_id, "V1")
    gotham.gcpd.add_suspect(case.case_id, "V1")
    assert case.suspects == ["V1"]
    with pytest.raises(NotFoundError):
        gotham.gcpd.add_suspect(case.case_id, "V404")


def test_solving_with_culprit_apprehends_them(gotham, make_villain):
    two_face = make_villain("V1", "Two-Face", 7)
    case = gotham.gcpd.open_case("Coin-toss robberies", District.OLD_GOTHAM, Severity.MAJOR, TODAY)
    gotham.gcpd.add_suspect(case.case_id, "V1")

    gotham.gcpd.solve(case.case_id, TODAY + timedelta(days=3), culprit_id="V1")

    assert case.status is CaseStatus.SOLVED
    assert case.closed_on == TODAY + timedelta(days=3)
    assert two_face.status is VillainStatus.IN_CUSTODY


def test_culprit_must_be_a_suspect(gotham, make_villain):
    make_villain("V1", "Two-Face", 7)
    case = gotham.gcpd.open_case("Coin-toss robberies", District.OLD_GOTHAM, Severity.MAJOR, TODAY)
    with pytest.raises(InvalidStateError):
        gotham.gcpd.solve(case.case_id, TODAY, culprit_id="V1")


def test_cannot_close_before_opening(gotham):
    case = gotham.gcpd.open_case("a", District.EAST_END, Severity.MINOR, TODAY)
    with pytest.raises(ValueError):
        gotham.gcpd.solve(case.case_id, TODAY - timedelta(days=1))


def test_unassigned_old_cases_go_cold(gotham):
    stale = gotham.gcpd.open_case("Stale", District.BURNSIDE, Severity.MINOR, TODAY - timedelta(days=90))
    worked = gotham.gcpd.open_case("Worked", District.BURNSIDE, Severity.MINOR, TODAY - timedelta(days=120))
    fresh = gotham.gcpd.open_case("Fresh", District.BURNSIDE, Severity.MINOR, TODAY - timedelta(days=89))
    gotham.gcpd.assign(worked.case_id, "Det. Renee Montoya")

    cold = gotham.gcpd.sweep_cold_cases(TODAY)

    assert cold == [stale]
    assert worked.status is CaseStatus.ASSIGNED
    assert fresh.status is CaseStatus.OPEN


def test_active_cases_sorted_by_severity_then_age(gotham):
    minor = gotham.gcpd.open_case("Graffiti", District.BURNSIDE, Severity.MINOR, TODAY - timedelta(days=10))
    major_new = gotham.gcpd.open_case("Heist", District.DIAMOND_DISTRICT, Severity.MAJOR, TODAY)
    major_old = gotham.gcpd.open_case("Kidnapping", District.EAST_END, Severity.MAJOR, TODAY - timedelta(days=2))
    done = gotham.gcpd.open_case("Solved", District.EAST_END, Severity.CITYWIDE, TODAY)
    gotham.gcpd.solve(done.case_id, TODAY)

    assert gotham.gcpd.active_cases() == [major_old, major_new, minor]


def test_caseload_counts_assigned_cases(gotham):
    for title in ("a", "b", "c"):
        case = gotham.gcpd.open_case(title, District.EAST_END, Severity.MINOR, TODAY)
        gotham.gcpd.assign(case.case_id, "Det. Montoya" if title != "b" else "Det. Allen")
    assert gotham.gcpd.caseload() == {"Det. Allen": 1, "Det. Montoya": 2}


def test_dossier(gotham, make_villain):
    make_villain("V1", "The Penguin", 6, associates=("Butch Gilzean", "Gabe"), real_name="Oswald Cobblepot")
    case = gotham.gcpd.open_case("Arms deal", District.EAST_END, Severity.SERIOUS, TODAY)
    gotham.gcpd.add_suspect(case.case_id, "V1")

    dossier = gotham.gcpd.dossier("V1")

    assert dossier == {
        "alias": "The Penguin",
        "real_name": "Oswald Cobblepot",
        "status": "at large",
        "threat_level": 6,
        "known_associates": ["Butch Gilzean", "Gabe"],
        "open_cases": [case.case_id],
    }


def test_dossier_lists_only_the_villains_own_associates(gotham):
    gotham.villains.save(Villain("V1", "The Riddler", "Edward Nygma", 7))
    joker = gotham.villains.save(Villain("V2", "The Joker", threat_level=10))

    joker.add_associate("Harley Quinn")

    assert gotham.gcpd.dossier("V1")["known_associates"] == []
    assert gotham.gcpd.dossier("V2")["known_associates"] == ["Harley Quinn"]
