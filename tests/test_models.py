from datetime import date, timedelta
from decimal import Decimal

import pytest

from gotham.models import Ally, Case, CaseStatus, District, Gadget, GadgetCategory, Inmate, Severity, Wing
from gotham.models.villain import Villain, VillainStatus


class TestVillain:
    def test_threat_level_is_validated(self):
        with pytest.raises(ValueError):
            Villain("V1", "Killer Croc", threat_level=0, known_associates=[])
        with pytest.raises(ValueError):
            Villain("V1", "Killer Croc", threat_level=11, known_associates=[])

    def test_alias_is_required(self):
        with pytest.raises(ValueError):
            Villain("V1", "", known_associates=[])

    def test_add_associate_ignores_duplicates(self, make_villain):
        joker = make_villain("V1", "The Joker", associates=("Harley Quinn",))
        joker.add_associate("Harley Quinn")
        joker.add_associate("Mr. J's goons")
        assert joker.known_associates == ["Harley Quinn", "Mr. J's goons"]

    def test_remove_associate(self, make_villain):
        joker = make_villain("V1", "The Joker", associates=("Harley Quinn",))
        joker.remove_associate("Harley Quinn")
        joker.remove_associate("Nobody")
        assert joker.known_associates == []

    def test_apprehend_only_when_at_large(self, make_villain):
        bane = make_villain("V1", "Bane", 9)
        bane.apprehend()
        assert bane.status is VillainStatus.IN_CUSTODY
        with pytest.raises(ValueError):
            bane.apprehend()

    def test_equality_is_by_id(self, make_villain):
        a = make_villain("V1", "Hush")
        b = Villain("V1", "Tommy Elliot", known_associates=[])
        assert a == b
        assert len({a, b}) == 1


class TestInmateAndWing:
    @pytest.mark.parametrize(
        "threat, wing",
        [(10, Wing.MAXIMUM), (8, Wing.MAXIMUM), (7, Wing.HIGH), (5, Wing.HIGH), (4, Wing.MEDIUM), (1, Wing.MEDIUM)],
    )
    def test_wing_for_threat(self, threat, wing):
        assert Wing.for_threat(threat) is wing

    def test_release_date_and_eligibility(self):
        inmate = Inmate("V1", Wing.HIGH, "B-01", date(2026, 1, 1), 30)
        assert inmate.release_date == date(2026, 1, 31)
        assert not inmate.is_eligible_for_release(date(2026, 1, 30))
        assert inmate.is_eligible_for_release(date(2026, 1, 31))
        assert inmate.days_served(date(2026, 1, 11)) == 10


class TestCase:
    def test_age_uses_close_date_when_closed(self):
        opened = date(2026, 1, 1)
        case = Case("GCPD-0001", "Bank job", District.EAST_END, Severity.SERIOUS, opened)
        assert case.age_in_days(opened + timedelta(days=5)) == 5
        case.status = CaseStatus.SOLVED
        case.closed_on = opened + timedelta(days=2)
        assert case.age_in_days(opened + timedelta(days=50)) == 2
        assert not case.is_active

    def test_cases_do_not_share_suspect_lists(self):
        a = Case("GCPD-0001", "a", District.EAST_END, Severity.MINOR, date(2026, 1, 1))
        b = Case("GCPD-0002", "b", District.EAST_END, Severity.MINOR, date(2026, 1, 1))
        a.suspects.append("V1")
        assert b.suspects == []


class TestGadgetAndAlly:
    def test_gadget_validation(self):
        with pytest.raises(ValueError):
            Gadget("Batarang", 0, GadgetCategory.THROWABLE)
        with pytest.raises(ValueError):
            Gadget("Batarang", 100, GadgetCategory.THROWABLE, Decimal("-1"))

    def test_ally_moves_and_has_skills(self):
        robin = Ally("A1", "Robin", District.WAYNE_MANOR, {"acrobatics"})
        robin.move_to(District.BURNSIDE)
        assert robin.location is District.BURNSIDE
        assert robin.has_skill("acrobatics")
        assert not robin.has_skill("hacking")
