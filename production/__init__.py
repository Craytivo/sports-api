"""Production football scoring and game-state integration layer."""

from .models import CanonicalGame
from .scoring import score_game

__all__ = ["CanonicalGame", "score_game"]
