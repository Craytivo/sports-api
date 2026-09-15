from __future__ import annotations

from typing import Sequence

from .models import CanonicalGame, Sport
from .provider import SportsProvider
from .ratings import TeamRatingsProvider, apply_team_ratings


class GameIngestion:
    """Application-level ingestion service.

    Providers are dependencies of ingestion only. Scoring receives canonical
    games and never imports or inspects a provider implementation.
    """

    def __init__(self, provider: SportsProvider, ratings_provider: TeamRatingsProvider | None = None) -> None:
        self.provider = provider
        self.ratings_provider = ratings_provider

    def fetch_games(self, sport: Sport, *, date: str | None = None, season: int | None = None) -> Sequence[CanonicalGame]:
        games = tuple(self.provider.fetch_games(sport, date=date))
        if self.ratings_provider is None or not games:
            return games
        ratings = self.ratings_provider.fetch_ratings(sport, season=season)
        return apply_team_ratings(games, ratings)
