"""Road network of Gotham and route planning for the Batmobile."""

from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass

from gotham.exceptions import NoRouteError
from gotham.models.district import District


@dataclass(frozen=True)
class Route:
    stops: tuple[District, ...]
    minutes: int

    @property
    def start(self) -> District:
        return self.stops[0]

    @property
    def end(self) -> District:
        return self.stops[-1]

    @property
    def hops(self) -> int:
        return len(self.stops) - 1


class CityMap:
    def __init__(self) -> None:
        self._roads: dict[District, dict[District, int]] = defaultdict(dict)
        self._closed: set[frozenset[District]] = set()

    def add_road(self, a: District, b: District, minutes: int, two_way: bool = True) -> None:
        if a is b:
            raise ValueError("A road must connect two different districts")
        if minutes <= 0:
            raise ValueError("Travel time must be positive")
        self._roads[a][b] = minutes
        if two_way:
            self._roads[b][a] = minutes

    def close_road(self, a: District, b: District) -> None:
        self._closed.add(frozenset((a, b)))

    def reopen_road(self, a: District, b: District) -> None:
        self._closed.discard(frozenset((a, b)))

    def is_closed(self, a: District, b: District) -> bool:
        return frozenset((a, b)) in self._closed

    def neighbours(self, district: District) -> dict[District, int]:
        return {
            other: minutes
            for other, minutes in self._roads.get(district, {}).items()
            if not self.is_closed(district, other)
        }

    def districts(self) -> set[District]:
        known = set(self._roads)
        for edges in self._roads.values():
            known.update(edges)
        return known

    def shortest_route(self, start: District, goal: District) -> Route:
        if start is goal:
            return Route((start,), 0)

        dist: dict[District, int] = {start: 0}
        previous: dict[District, District] = {}
        visited: set[District] = set()
        frontier: list[tuple[int, str, District]] = [(0, start.name, start)]

        while frontier:
            minutes, _, district = heapq.heappop(frontier)
            if district in visited:
                continue
            visited.add(district)
            if district is goal:
                break
            for neighbour, cost in self.neighbours(district).items():
                if neighbour not in dist:
                    dist[neighbour] = minutes + cost
                    previous[neighbour] = district
                    heapq.heappush(frontier, (dist[neighbour], neighbour.name, neighbour))

        if goal not in dist:
            raise NoRouteError(start, goal)

        stops = [goal]
        while stops[-1] is not start:
            stops.append(previous[stops[-1]])
        return Route(tuple(reversed(stops)), dist[goal])

    def travel_time(self, start: District, goal: District) -> int:
        return self.shortest_route(start, goal).minutes

    def patrol(self, start: District, checkpoints: list[District]) -> Route:
        """Visit each checkpoint in order and return to start."""
        stops: list[District] = [start]
        total = 0
        for target in [*checkpoints, start]:
            leg = self.shortest_route(stops[-1], target)
            stops.extend(leg.stops[1:])
            total += leg.minutes
        return Route(tuple(stops), total)
