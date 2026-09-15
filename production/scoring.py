from __future__ import annotations

from typing import Any

from simulator.features import FeatureSnapshot, calculate_features
from simulator.scorer import MODEL_VERSION, score_features

from .models import CanonicalGame


# Production boundary for the frozen V1 scoring contract.
# The simulator remains the behavioral oracle during the integration phase;
# this entry point accepts only the canonical game model so providers never
# couple directly to scoring internals.
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
