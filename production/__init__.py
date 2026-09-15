"""Production football scoring and game-state integration layer."""

from .ingestion import GameIngestion
from .models import CanonicalGame
from .provider import SportsProvider
from .ratings import ESPNPowerIndexRatingsProvider, TeamRating, TeamRatingsProvider
from .scoring import score_game

__all__ = [
    "CanonicalGame",
    "ESPNPowerIndexRatingsProvider",
    "GameIngestion",
    "SportsProvider",
    "TeamRating",
    "TeamRatingsProvider",
    "score_game",
]
