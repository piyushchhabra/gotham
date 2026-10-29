import pytest

from gotham.exceptions import InvalidStateError, NoAllyAvailableError
from gotham.models.case import Severity
from gotham.models.district import District as D


def build_simple_map(city):
    city.add_road(D.BATCAVE, D.OLD_GOTHAM, 5)
    city.add_road(D.OLD_GOTHAM, D.THE_NARROWS, 4)
    city.add_road(D.BURNSIDE, D.THE_NARROWS, 15)
    city.add_road(D.GCPD_HQ, D.OLD_GOTHAM, 3)


def build_downtown_map(city):
    city.add_road(D.BATCAVE, D.OLD_GOTHAM, 5)
    city.add_road(D.OLD_GOTHAM, D.THE_NARROWS, 20)
    city.add_road(D.BATCAVE, D.DIAMOND_DISTRICT, 6)
    city.add_road(D.DIAMOND_DISTRICT, D.EAST_END, 4)
    city.add_road(D.EAST_END, D.THE_NARROWS, 3)
    city.add_road(D.BURNSIDE, D.THE_NARROWS, 18)
    city.add_road(D.ARKHAM_ISLAND, D.THE_NARROWS, 22)


def test_dispatches_closest_available_ally(gotham, make_ally):
    build_simple_map(gotham.city_map)
    make_ally("A1", "Batman", D.BATCAVE)
    make_ally("A2", "Nightwing", D.BURNSIDE)

    dispatch = gotham.bat_signal.raise_signal(D.THE_NARROWS)

    assert dispatch.codename == "Batman"
    assert dispatch.eta_minutes == 9
    assert dispatch.route.stops == (D.BATCAVE, D.OLD_GOTHAM, D.THE_NARROWS)
    assert not gotham.allies.get("A1").available


def test_dispatches_ally_with_shortest_eta_across_downtown(gotham, make_ally):
    build_downtown_map(gotham.city_map)
    make_ally("A1", "Batman", D.BATCAVE)
    make_ally("A2", "Nightwing", D.BURNSIDE)

    dispatch = gotham.bat_signal.raise_signal(D.THE_NARROWS, Severity.MAJOR)

    assert dispatch.codename == "Batman"
    assert dispatch.eta_minutes == 13
    assert dispatch.route.stops == (D.BATCAVE, D.DIAMOND_DISTRICT, D.EAST_END, D.THE_NARROWS)


def test_citywide_alert_sends_the_fastest_responders(gotham, make_ally):
    build_downtown_map(gotham.city_map)
    make_ally("A1", "Batman", D.BATCAVE)
    make_ally("A2", "Nightwing", D.BURNSIDE)
    make_ally("A3", "Robin", D.ARKHAM_ISLAND)

    dispatches = gotham.bat_signal.raise_citywide_alert(D.THE_NARROWS, responders=2)

    assert [d.codename for d in dispatches] == ["Batman", "Nightwing"]
    assert [d.eta_minutes for d in dispatches] == [13, 18]
    assert gotham.allies.get("A3").available


def test_equal_eta_is_broken_by_codename(gotham, make_ally):
    gotham.city_map.add_road(D.OLD_GOTHAM, D.GCPD_HQ, 4)
    gotham.city_map.add_road(D.EAST_END, D.GCPD_HQ, 4)
    make_ally("A1", "Red Hood", D.EAST_END)
    make_ally("A2", "Batgirl", D.OLD_GOTHAM)

    assert gotham.bat_signal.raise_signal(D.GCPD_HQ).codename == "Batgirl"


def test_required_skill_filters_allies(gotham, make_ally):
    build_simple_map(gotham.city_map)
    make_ally("A1", "Batman", D.BATCAVE, "combat")
    make_ally("A2", "Oracle", D.GCPD_HQ, "hacking")

    dispatch = gotham.bat_signal.raise_signal(D.THE_NARROWS, required_skill="hacking")

    assert dispatch.codename == "Oracle"
    assert dispatch.eta_minutes == 7


def test_busy_allies_are_skipped(gotham, make_ally):
    build_simple_map(gotham.city_map)
    make_ally("A1", "Batman", D.BATCAVE)
    make_ally("A2", "Nightwing", D.BURNSIDE)

    first = gotham.bat_signal.raise_signal(D.THE_NARROWS)
    second = gotham.bat_signal.raise_signal(D.THE_NARROWS)

    assert (first.codename, second.codename) == ("Batman", "Nightwing")
    assert len(gotham.bat_signal.active) == 2


def test_unreachable_allies_are_skipped(gotham, make_ally):
    build_simple_map(gotham.city_map)
    make_ally("A1", "Batman", D.OTISBURG)
    with pytest.raises(NoAllyAvailableError):
        gotham.bat_signal.raise_signal(D.THE_NARROWS)


def test_stand_down_frees_ally_at_incident_location(gotham, make_ally):
    build_simple_map(gotham.city_map)
    make_ally("A1", "Batman", D.BATCAVE)
    gotham.bat_signal.raise_signal(D.THE_NARROWS)

    batman = gotham.bat_signal.stand_down("A1")

    assert batman.available
    assert batman.location is D.THE_NARROWS
    assert gotham.bat_signal.active == []
    assert len(gotham.bat_signal.history) == 1


def test_stand_down_requires_active_mission(gotham, make_ally):
    make_ally("A1", "Batman", D.BATCAVE)
    with pytest.raises(InvalidStateError):
        gotham.bat_signal.stand_down("A1")


def test_citywide_alert_needs_enough_allies(gotham, make_ally):
    build_simple_map(gotham.city_map)
    make_ally("A1", "Batman", D.BATCAVE)
    with pytest.raises(NoAllyAvailableError):
        gotham.bat_signal.raise_citywide_alert(D.THE_NARROWS, responders=2)
