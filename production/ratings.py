from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Protocol

from .models import CanonicalGame, Sport, TeamState


@dataclass(frozen=True)
class TeamRating:
    team_id: str
    strength: float
    source: str
    season: int


class TeamRatingsProvider(Protocol):
    name: str

    def fetch_ratings(self, sport: Sport, *, season: int | None = None) -> dict[str, TeamRating]:
        ...


class ESPNPowerIndexRatingsProvider:
    """Loads ESPN Power Index ratings and maps them to the canonical 0-100 strength field.

    This is an input-data integration layer only. It does not alter the frozen
    Game Score weights, calibration, or scoring formulas.
    """

    name = "espn-powerindex"
    _BASE = "https://sports.core.api.espn.com/v2/sports/football/leagues"
    _LEAGUES = {"NFL": "nfl", "NCAA_FOOTBALL": "college-football"}

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_ratings(self, sport: Sport, *, season: int | None = None) -> dict[str, TeamRating]:
        league = self._LEAGUES.get(sport)
        if league is None:
            raise ValueError(f"Unsupported sport: {sport}")
        season = season or datetime.now().year
        url = f"{self._BASE}/{league}/seasons/{season}/powerindex"
        request = Request(url, headers={"User-Agent": "sports-api/1.0"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.load(response)
        rows = self._rows(payload)
        values: list[tuple[str, float]] = []
        for row in rows:
            team_id = self._team_id(row)
            value = self._fpi(row)
            if team_id is not None and value is not None:
                values.append((team_id, value))
        if not values:
            return {}
        low = min(value for _, value in values)
        high = max(value for _, value in values)
        span = high - low
        ratings: dict[str, TeamRating] = {}
        for team_id, value in values:
            strength = 50.0 if span == 0 else 100.0 * (value - low) / span
            ratings[team_id] = TeamRating(team_id, strength, self.name, season)
        return ratings

    @staticmethod
    def _rows(payload: dict) -> list[dict]:
        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        return []

    @staticmethod
    def _team_id(row: dict) -> str | None:
        team = row.get("team")
        if isinstance(team, dict) and team.get("id") is not None:
            return str(team["id"])
        for key in ("team_ref", "teamRef", "$ref"):
            value = row.get(key)
            if value:
                match = re.search(r"/teams/(\d+)", str(value))
                if match:
                    return match.group(1)
        return None

    @staticmethod
    def _fpi(row: dict) -> float | None:
        for key in ("fpi", "value", "rating"):
            value = row.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        metrics = row.get("metrics")
        if isinstance(metrics, list):
            for metric in metrics:
                if isinstance(metric, dict) and str(metric.get("name", metric.get("abbreviation", ""))).lower() == "fpi":
                    value = metric.get("value")
                    if isinstance(value, (int, float)):
                        return float(value)
        return None


def apply_team_ratings(
    games: list[CanonicalGame] | tuple[CanonicalGame, ...],
    ratings: dict[str, TeamRating],
) -> tuple[CanonicalGame, ...]:
    """Return canonical games enriched with external team strength inputs."""
    enriched: list[CanonicalGame] = []
    for game in games:
        home_rating = ratings.get(game.home.id)
        away_rating = ratings.get(game.away.id)
        home = game.home if home_rating is None else TeamState(
            id=game.home.id,
            name=game.home.name,
            strength=home_rating.strength,
            rank=game.home.rank,
        )
        away = game.away if away_rating is None else TeamState(
            id=game.away.id,
            name=game.away.name,
            strength=away_rating.strength,
            rank=game.away.rank,
        )
        enriched.append(
            CanonicalGame(
                id=game.id,
                sport=game.sport,
                phase=game.phase,
                home=home,
                away=away,
                state=game.state,
                context=game.context,
                history=game.history,
                events=game.events,
                source=game.source,
                source_updated_at=game.source_updated_at,
            )
        )
    return tuple(enriched)
