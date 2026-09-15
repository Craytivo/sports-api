"""Production football scoring and game-state integration layer."""

from .ingestion import GameIngestion
from .models import CanonicalGame
from .provider import SportsProvider
from .scoring import score_game

__all__ = ["CanonicalGame", "GameIngestion", "SportsProvider", "score_game"]
