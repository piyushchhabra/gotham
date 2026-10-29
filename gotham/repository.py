from __future__ import annotations

from typing import Callable, Generic, Iterator, TypeVar

from gotham.exceptions import NotFoundError

T = TypeVar("T")
K = TypeVar("K")


class InMemoryRepository(Generic[K, T]):
    """Insertion-ordered key/value store used by all services."""

    def __init__(self, kind: str, key: Callable[[T], K]) -> None:
        self._kind = kind
        self._key = key
        self._items: dict[K, T] = {}

    def save(self, item: T) -> T:
        self._items[self._key(item)] = item
        return item

    def get(self, key: K) -> T:
        try:
            return self._items[key]
        except KeyError:
            raise NotFoundError(self._kind, key) from None

    def find(self, key: K) -> T | None:
        return self._items.get(key)

    def exists(self, key: K) -> bool:
        return key in self._items

    def delete(self, key: K) -> None:
        if self._items.pop(key, None) is None:
            raise NotFoundError(self._kind, key)

    def all(self) -> list[T]:
        return list(self._items.values())

    def filter(self, predicate: Callable[[T], bool]) -> list[T]:
        return [item for item in self._items.values() if predicate(item)]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(list(self._items.values()))
