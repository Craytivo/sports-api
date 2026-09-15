from __future__ import annotations
from .features import FeatureSnapshot, clamp

MODEL_VERSION = "football-lab-v1.3"


def calibrate(raw: float, competitiveness: float) -> float:
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


def pregame_score(f: FeatureSnapshot) -> float:
    """Pregame expectation: matchup quality matters, but elite stakes can lift it."""
    # A very weak matchup should not score highly merely because its winner is
    # uncertain. Team quality therefore shapes expected competitiveness
    # nonlinearly before observed game state exists.
    matchup_quality = 100.0 * (f.team_quality / 100.0) ** 1.9
    expected_competitiveness = matchup_quality * (0.40 + 0.60 * f.outcome_uncertainty / 100.0)
    raw = (
        0.40 * expected_competitiveness
        + 0.25 * f.team_quality
        + 0.20 * f.stakes
        + 0.15 * f.performance_quality
    )
    if f.team_quality > 80 and f.outcome_uncertainty > 80:
        raw += 2.0
    return clamp(raw)


def score_features(
    f: FeatureSnapshot,
    game_state: dict | None = None,
    context: dict | None = None,
    phase: str | None = None,
) -> dict[str, float]:
    state = game_state or {}
    context = context or {}

    # Pregame is an expectation model, not a live-state model.
    if phase == "PREGAME":
        raw = pregame_score(f)
        score = raw
        return {
            "competitiveness": clamp(f.outcome_uncertainty),
            "game_quality": clamp(f.performance_quality),
            "team_quality": clamp(f.team_quality),
            "stakes": clamp(f.stakes),
            "drama": 0.0,
            "raw_score": round(raw, 2),
            "game_score": round(score, 2),
        }

    margin_state = 0.55 * f.margin_competitiveness + 0.45 * f.competitive_state
    competitiveness = (
        0.45 * f.outcome_uncertainty
        + 0.25 * (f.late_game_pressure * (0.35 + 0.65 * f.outcome_uncertainty / 100.0))
        + 0.20 * margin_state
        + 0.10 * f.competitive_history
    )

    # A completed game should retain the quality of the competitive journey.
    # This prevents a dramatic comeback from collapsing to a low score simply
    # because final-state win probability is 100/0.
    if phase == "FINAL" and f.competitive_history >= 40:
        competitiveness = max(competitiveness, 70.0)

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
    margin = f.margin_competitiveness
    uncertainty = f.outcome_uncertainty
    points = state.get("home_score", 0) + state.get("away_score", 0)

    if margin < 20 and uncertainty < 10:
        calibrated = min(calibrated, 15.0)
    elif margin < 35 and uncertainty < 10 and f.late_game_pressure > 50:
        calibrated = min(calibrated, 30.0)
    elif margin < 35 and uncertainty < 25 and f.late_game_pressure > 50:
        calibrated = min(calibrated, 35.0)

    if abs(state.get("home_score", 0) - state.get("away_score", 0)) >= 14 and state.get("quarter", 1) <= 2:
        calibrated = min(calibrated, 55.0)

    if points <= 3 and f.late_game_pressure > 50:
        calibrated = min(calibrated, 70.0)

    if (
        context.get("game_stage") in {"SUPER_BOWL", "NCAA_NATIONAL_CHAMPIONSHIP"}
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
