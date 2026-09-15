from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models import CanonicalGame, GameContext, GameState, Sport, TeamState


class ESPNProvider:
    """ESPN scoreboard adapter for NFL and NCAA Football.

    ESPN-specific payload parsing is intentionally confined to this module.
    The rest of the application receives only CanonicalGame objects.
    """

    name = "espn"
    _BASE = "https://site.api.espn.com/apis/site/v2/sports/football"
    _LEAGUES = {
        "NFL": "nfl",
        "NCAA_FOOTBALL": "college-football",
    }

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_games(self, sport: Sport, *, date: str | None = None) -> list[CanonicalGame]:
        try:
            league = self._LEAGUES[sport]
        except KeyError as exc:
            raise ValueError(f"Unsupported sport: {sport}") from exc

        params = {"limit": "1000"}
        if date:
            params["dates"] = date.replace("-", "")
        url = f"{self._BASE}/{league}/scoreboard?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": "sports-api/1.0"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.load(response)

        fetched_at = datetime.now(timezone.utc).isoformat()
        return [self._game_from_event(event, sport, fetched_at) for event in payload.get("events", [])]

    def _game_from_event(self, event: dict, sport: Sport, fetched_at: str) -> CanonicalGame:
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        status = competition.get("status", event.get("status", {}))
        state = status.get("type", {})
        state_name = state.get("name", "STATUS_SCHEDULED")
        completed = bool(state.get("completed"))
        phase = "FINAL" if completed else ("PREGAME" if state_name in {"STATUS_SCHEDULED", "STATUS_POSTPONED", "STATUS_CANCELED"} else "LIVE")

        period = int(status.get("period") or 1)
        clock = self._clock_seconds(status.get("displayClock"))
        if phase == "PREGAME":
            period, clock = 1, 3600
        elif phase == "FINAL":
            period, clock = 4, 0

        state_obj = GameState(
            quarter=period,
            seconds_remaining=clock,
            home_score=self._score(home),
            away_score=self._score(away),
        )
        context = GameContext(game_stage=self._game_stage(event, sport))
        return CanonicalGame(
            id=str(event.get("id")),
            sport=sport,
            phase=phase,
            home=self._team(home),
            away=self._team(away),
            state=state_obj,
            context=context,
            source=self.name,
            source_updated_at=fetched_at,
        )

    @staticmethod
    def _team(competitor: dict) -> TeamState:
        team = competitor.get("team", {})
        rank = competitor.get("curatedRank", {}).get("current")
        return TeamState(
            id=str(team.get("id") or competitor.get("id")),
            name=team.get("displayName") or team.get("shortDisplayName") or "Unknown",
            strength=50.0,
            rank=rank if isinstance(rank, int) else None,
        )

    @staticmethod
    def _score(competitor: dict) -> int:
        try:
            return int(competitor.get("score") or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _clock_seconds(clock: str | None) -> int:
        if not clock:
            return 0
        try:
            minutes, seconds = clock.split(":", 1)
            return max(0, int(minutes) * 60 + int(float(seconds)))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _game_stage(event: dict, sport: Sport) -> str:
        season_type = event.get("season", {}).get("slug", "")
        if sport == "NFL":
            if "post" in season_type:
                return "WILD_CARD"
            return "REGULAR_SEASON"
        return "NCAA_REGULAR_SEASON"
