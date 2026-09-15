from __future__ import annotations

from typing import Protocol, Sequence

from .models import CanonicalGame, Sport


class SportsProvider(Protocol):
    """Provider-neutral contract for football data ingestion.

    Implementations translate provider payloads into CanonicalGame objects.
    Nothing below this boundary should know provider field names, status codes,
    team identifiers, or endpoint shapes.
    """

    name: str

    def fetch_games(self, sport: Sport, *, date: str | None = None) -> Sequence[CanonicalGame]:
        ...
