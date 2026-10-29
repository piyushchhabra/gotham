"""The Bat-Signal: send the closest available ally to an incident."""

from __future__ import annotations

from dataclasses import dataclass

from gotham.exceptions import InvalidStateError, NoAllyAvailableError, NoRouteError
from gotham.models.ally import Ally
from gotham.models.case import Severity
from gotham.models.district import District
from gotham.repository import InMemoryRepository
from gotham.services.patrol import CityMap, Route


@dataclass(frozen=True)
class Dispatch:
    ally_id: str
    codename: str
    district: District
    severity: Severity
    route: Route

    @property
    def eta_minutes(self) -> int:
        return self.route.minutes


class BatSignal:
    def __init__(self, allies: InMemoryRepository[str, Ally], city: CityMap) -> None:
        self._allies = allies
        self._city = city
        self._active: dict[str, Dispatch] = {}
        self._history: list[Dispatch] = []

    def candidates(self, district: District, required_skill: str | None = None) -> list[tuple[Ally, Route]]:
        """Available allies who can reach the district, fastest first (ties by codename)."""
        options = []
        for ally in self._allies:
            if not ally.available:
                continue
            if required_skill and not ally.has_skill(required_skill):
                continue
            try:
                route = self._city.shortest_route(ally.location, district)
            except NoRouteError:
                continue
            options.append((ally, route))
        options.sort(key=lambda option: (option[1].minutes, option[0].codename))
        return options

    def raise_signal(
        self,
        district: District,
        severity: Severity = Severity.SERIOUS,
        required_skill: str | None = None,
    ) -> Dispatch:
        options = self.candidates(district, required_skill)
        if not options:
            raise NoAllyAvailableError(f"Nobody can answer the signal in {district}")
        ally, route = options[0]
        return self._dispatch(ally, district, severity, route)

    def raise_citywide_alert(self, district: District, responders: int) -> list[Dispatch]:
        options = self.candidates(district)
        if len(options) < responders:
            raise NoAllyAvailableError(f"Only {len(options)} allies can reach {district}")
        return [self._dispatch(ally, district, Severity.CITYWIDE, route) for ally, route in options[:responders]]

    def stand_down(self, ally_id: str) -> Ally:
        dispatch = self._active.pop(ally_id, None)
        if dispatch is None:
            raise InvalidStateError(f"{ally_id} is not on a mission")
        ally = self._allies.get(ally_id)
        ally.move_to(dispatch.district)
        ally.available = True
        return ally

    @property
    def active(self) -> list[Dispatch]:
        return list(self._active.values())

    @property
    def history(self) -> list[Dispatch]:
        return list(self._history)

    def _dispatch(self, ally: Ally, district: District, severity: Severity, route: Route) -> Dispatch:
        dispatch = Dispatch(ally.ally_id, ally.codename, district, severity, route)
        ally.available = False
        self._active[ally.ally_id] = dispatch
        self._history.append(dispatch)
        return dispatch
