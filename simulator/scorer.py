from __future__ import annotations
from .features import FeatureSnapshot, clamp

MODEL_VERSION = "football-lab-v1.2"


def calibrate(raw: float, competitiveness: float) -> float:
    """Map the lab raw score into the product's 0-100 attention scale.

    The curve is deliberately progressive: weakly competitive games do not get
    inflated into elite territory, while genuinely competitive states get more
    resolution near the top of the scale.
    """
    if raw <= 0:
        return 0.0
    if competitiveness >= 70:
        exponent = 0.13
    elif competitiveness >= 60:
        exponent = 0.50
    elif competitiveness >= 55:
        exponent = 0.40
    else:
        exponent = 0.85
    return clamp(100.0 * (raw / 100.0) ** exponent)


def score_features(f: FeatureSnapshot, game_state: dict | None = None, context: dict | None = None) -> dict[str, float]:
    margin_state = 0.55 * f.margin_competitiveness + 0.45 * f.competitive_state
    competitiveness = (
        0.45 * f.outcome_uncertainty
        + 0.25 * (f.late_game_pressure * (0.35 + 0.65 * f.outcome_uncertainty / 100.0))
        + 0.20 * margin_state
        + 0.10 * f.competitive_history
    )
    game_quality = (
        0.30 * f.scoring_action
        + 0.25 * f.explosive_play_rate
        + 0.25 * f.high_leverage_event_rate
        + 0.20 * f.performance_quality
    )
    drama = clamp(
        0.50 * f.wp_volatility
        + 0.30 * f.recent_score_movement
        + 0.20 * f.momentum_swing
        + 0.10 * f.competitive_history
    )
    raw = (
        0.50 * competitiveness
        + 0.15 * game_quality
        + 0.15 * f.team_quality
        + 0.10 * f.stakes
        + 0.10 * drama
    )

    calibrated = calibrate(raw, competitiveness)

    # Guardrails preserve the product hierarchy: actual competitive state beats
    # prestige, and a dead game cannot remain elite because it is important.
    margin = f.margin_competitiveness
    uncertainty = f.outcome_uncertainty
    state = game_state or {}
    points = state.get("home_score", 0) + state.get("away_score", 0)

    if margin < 20 and uncertainty < 10:
        calibrated = min(calibrated, 15.0)
    elif margin < 35 and uncertainty < 10 and f.late_game_pressure > 50:
        calibrated = min(calibrated, 30.0)
    elif margin < 35 and uncertainty < 25 and f.late_game_pressure > 50:
        calibrated = min(calibrated, 35.0)

    # Early two-score games should remain interesting but not become late-game
    # contenders merely because the scoring total is high.
    if abs(state.get("home_score", 0) - state.get("away_score", 0)) >= 14 and state.get("quarter", 1) <= 2:
        calibrated = min(calibrated, 55.0)

    # A scoreless/near-scoreless game can be tense, but the absence of action is
    # itself meaningful. Preserve the anchor's 45-70 range.
    if points <= 3 and f.late_game_pressure > 50:
        calibrated = min(calibrated, 70.0)

    # Championship context can push an already exceptional competitive game into
    # the canonical upper band; it cannot rescue a noncompetitive game.
    if (
        context
        and context.get("game_stage") in {"SUPER_BOWL", "NCAA_NATIONAL_CHAMPIONSHIP"}
        and competitiveness >= 70
    ):
        calibrated = clamp(calibrated + 1.5)

    return {
        "competitiveness": clamp(competitiveness),
        "game_quality": clamp(game_quality),
        "team_quality": clamp(f.team_quality),
        "stakes": clamp(f.stakes),
        "drama": clamp(drama),
        "raw_score": clamp(raw),
        "game_score": round(clamp(calibrated), 2),
    }
