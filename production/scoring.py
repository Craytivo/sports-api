from __future__ import annotations

import math
from typing import Any

from simulator.features import FeatureSnapshot, calculate_features
from simulator.scorer import score_features, MODEL_VERSION

from .models import CanonicalGame


@dataclass
class ScoreResult:
    game_id: str
    game_score: float
    model_version: str
    phase: str
    features: dict[str, float]
    components: dict[str, float]


# Production entry point. The frozen lab model remains the behavioral oracle
# until the production feature engine is independently extracted and parity-
# tested. This adapter deliberately accepts only the canonical game contract.
def score_game(game: CanonicalGame) -> dict[str, Any]:
    features: FeatureSnapshot = calculate_features(game.scoring_input())
    scored = score_features(
        features,
        game_state=game.state.as_dict(),
        context=game.context.as_dict(),
        phase=game.phase,
    )
    return {
        "game_id": game.id,
        "game_score": scored["game_score"],
        "model_version": MODEL_VERSION,
        "phase": game.phase,
        "features": features.as_dict(),
        "components": {
            "competitiveness": scored["competitiveness"],
            "game_quality": scored["game_quality"],
            "team_quality": scored["team_quality"],
            "stakes": scored["stakes"],
            "drama": scored["drama"],
        },
        "raw_score": scored["raw_score"],
    }
