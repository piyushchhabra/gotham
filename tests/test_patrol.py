import pytest

from gotham.exceptions import NoRouteError
from gotham.models.district import District as D
from gotham.services.patrol import CityMap


@pytest.fixture
def city() -> CityMap:
    city = CityMap()
    city.add_road(D.BATCAVE, D.OLD_GOTHAM, 2)
    city.add_road(D.OLD_GOTHAM, D.THE_NARROWS, 3)
    city.add_road(D.BATCAVE, D.EAST_END, 4)
    city.add_road(D.EAST_END, D.THE_NARROWS, 10)
    city.add_road(D.THE_NARROWS, D.ARKHAM_ISLAND, 6)
    return city


def test_route_to_same_district_is_free(city):
    route = city.shortest_route(D.BATCAVE, D.BATCAVE)
    assert route.stops == (D.BATCAVE,)
    assert route.minutes == 0


def test_direct_neighbour(city):
    route = city.shortest_route(D.BATCAVE, D.OLD_GOTHAM)
    assert route.stops == (D.BATCAVE, D.OLD_GOTHAM)
    assert route.minutes == 2


def test_prefers_the_faster_of_two_routes(city):
    route = city.shortest_route(D.BATCAVE, D.THE_NARROWS)
    assert route.stops == (D.BATCAVE, D.OLD_GOTHAM, D.THE_NARROWS)
    assert route.minutes == 5


def test_multi_hop_route(city):
    route = city.shortest_route(D.BATCAVE, D.ARKHAM_ISLAND)
    assert route.stops == (D.BATCAVE, D.OLD_GOTHAM, D.THE_NARROWS, D.ARKHAM_ISLAND)
    assert route.minutes == 11
    assert route.hops == 3


def test_roads_are_two_way_by_default(city):
    assert city.travel_time(D.ARKHAM_ISLAND, D.BATCAVE) == 11


def test_one_way_roads(city):
    city.add_road(D.ACE_CHEMICALS, D.EAST_END, 3, two_way=False)
    assert city.travel_time(D.ACE_CHEMICALS, D.EAST_END) == 3
    with pytest.raises(NoRouteError):
        city.shortest_route(D.EAST_END, D.ACE_CHEMICALS)


def test_closed_road_forces_detour(city):
    city.close_road(D.OLD_GOTHAM, D.THE_NARROWS)
    route = city.shortest_route(D.BATCAVE, D.THE_NARROWS)
    assert route.stops == (D.BATCAVE, D.EAST_END, D.THE_NARROWS)
    assert route.minutes == 14

    city.reopen_road(D.THE_NARROWS, D.OLD_GOTHAM)
    assert city.travel_time(D.BATCAVE, D.THE_NARROWS) == 5


def test_unreachable_district(city):
    with pytest.raises(NoRouteError):
        city.shortest_route(D.BATCAVE, D.OTISBURG)


def test_patrol_visits_checkpoints_and_returns(city):
    route = city.patrol(D.BATCAVE, [D.OLD_GOTHAM, D.THE_NARROWS])
    assert route.stops == (D.BATCAVE, D.OLD_GOTHAM, D.THE_NARROWS, D.OLD_GOTHAM, D.BATCAVE)
    assert route.minutes == 10


def test_invalid_roads(city):
    with pytest.raises(ValueError):
        city.add_road(D.BATCAVE, D.BATCAVE, 1)
    with pytest.raises(ValueError):
        city.add_road(D.BATCAVE, D.BURNSIDE, 0)


def test_known_districts(city):
    assert city.districts() == {D.BATCAVE, D.OLD_GOTHAM, D.THE_NARROWS, D.EAST_END, D.ARKHAM_ISLAND}
