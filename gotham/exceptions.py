class GothamError(Exception):
    """Base class for all domain errors."""


class NotFoundError(GothamError):
    def __init__(self, kind: str, identifier: object) -> None:
        super().__init__(f"{kind} not found: {identifier}")
        self.kind = kind
        self.identifier = identifier


class CapacityError(GothamError):
    """Raised when something is full: a utility belt, an Arkham wing, a budget."""


class InvalidStateError(GothamError):
    """Raised when an operation is not allowed in the entity's current state."""


class NoRouteError(GothamError):
    def __init__(self, start: object, goal: object) -> None:
        super().__init__(f"No route from {start} to {goal}")
        self.start = start
        self.goal = goal


class NoAllyAvailableError(GothamError):
    """Raised when the Bat-Signal goes up and nobody can answer it."""
