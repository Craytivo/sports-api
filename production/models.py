from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Sport = Literal["NFL", "NCAA_FOOTBALL"]
Phase = Literal["PREGAME", "LIVE", "FINAL"]


@dataclass(frozen=True)
class TeamState:
    id: str
    name: str
    strength: float = 50.0
    rank: int | None = None


@dataclass(frozen=True)
class GameState:
    quarter: int = 1
    seconds_remaining: int = 3600
    home_score: int = 0
    away_score: int = 0
    possession: str | None = None
    down: int | None = None
    distance: float | None = None
    field_position_yards_to_goal: float | None = None
    home_timeouts: int | None = None
    away_timeouts: int | None = None
    home_win_probability: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass(frozen=True)
class GameContext:
    game_stage: str = "REGULAR_SEASON"
    playoff_impact: str = "UNKNOWN"
    rivalry: str = "NONE"
    historical_context: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class GameEvent:
    type: str
    points: int = 0
    wp_change: float = 0.0
    explosive: bool = False
    timestamp: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass(frozen=True)
class GameHistory:
    elapsed_seconds: int = 0
    close_game_seconds: int = 0
    lead_changes: int = 0
    ties: int = 0
    comeback_events: int = 0
    largest_lead: int = 0

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class CanonicalGame:
    id: str
    sport: Sport
    phase: Phase
    home: TeamState
    away: TeamState
    state: GameState = field(default_factory=GameState)
    context: GameContext = field(default_factory=GameContext)
    history: GameHistory = field(default_factory=GameHistory)
    events: tuple[GameEvent, ...] = ()
    source: str | None = None
    source_updated_at: str | None = None

    def scoring_input(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sport": self.sport,
            "phase": self.phase,
            "game_state": self.state.as_dict(),
            "teams": {
                "home_strength": self.home.strength,
                "away_strength": self.away.strength,
            },
            "context": self.context.as_dict(),
            "history": self.history.as_dict(),
            "events": [event.as_dict() for event in self.events],
        }
