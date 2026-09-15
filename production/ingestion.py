from __future__ import annotations

from typing import Sequence

from .models import CanonicalGame, Sport
from .provider import SportsProvider


class GameIngestion:
    """Application-level ingestion service.

    Providers are dependencies of ingestion only. Scoring receives canonical
    games and never imports or inspects a provider implementation.
    """

    def __init__(self, provider: SportsProvider) -> None:
        self.provider = provider

    def fetch_games(self, sport: Sport, *, date: str | None = None) -> Sequence[CanonicalGame]:
        games = self.provider.fetch_games(sport, date=date)
        return tuple(games)
