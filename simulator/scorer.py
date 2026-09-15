from __future__ import annotations
from .features import FeatureSnapshot, clamp

MODEL_VERSION = "football-lab-v1.8"


def calibrate(raw: float, competitiveness: float) -> float:
    if raw <= 0: return 0.0
    if competitiveness >= 70: exponent = 0.13
    elif competitiveness >= 65: exponent = 0.20
    elif competitiveness >= 60: exponent = 0.50
    elif competitiveness >= 55: exponent = 0.40
    else: exponent = 0.85
    return clamp(100.0 * (raw / 100.0) ** exponent)


def pregame_score(f: FeatureSnapshot) -> float:
    matchup_quality = 100.0 * (f.team_quality / 100.0) ** 2.3
    expected_competitiveness = matchup_quality * (0.40 + 0.60 * f.outcome_uncertainty / 100.0)
    # Pregame has no observed performance yet. Use a team-quality-derived
    # expectation instead of the live-game performance baseline.
    expected_game_quality = clamp(30.0 + 0.55 * f.team_quality)
    raw = 0.40 * expected_competitiveness + 0.25 * f.team_quality + 0.20 * f.stakes + 0.15 * expected_game_quality
    if f.team_quality > 80 and f.outcome_uncertainty > 80: raw += 2.0
    return clamp(raw)


def score_features(f: FeatureSnapshot, game_state: dict | None = None, context: dict | None = None, phase: str | None = None) -> dict[str, float]:
    state = game_state or {}; context = context or {}
    if phase == "PREGAME":
        raw = pregame_score(f)
        return {"competitiveness": clamp(f.outcome_uncertainty), "game_quality": clamp(f.performance_quality), "team_quality": clamp(f.team_quality), "stakes": clamp(f.stakes), "drama": 0.0, "raw_score": round(raw, 2), "game_score": round(raw, 2)}

    competitiveness = f.competitiveness
    # A documented comeback arc is itself evidence that the live state is
    # unusually compelling, even before the game reaches the late-game window.
    if phase != "FINAL":
        comeback_events = min(3, int((state.get("comeback_events") or 0)))
        competitiveness = clamp(competitiveness + 0.35 * comeback_events)
    if phase == "FINAL" and f.competitive_history >= 40:
        competitiveness = max(competitiveness, 70.0)

    game_quality = 0.30 * f.scoring_action + 0.25 * f.explosive_play_rate + 0.25 * f.high_leverage_event_rate + 0.20 * f.performance_quality
    drama = clamp(0.50 * f.wp_volatility + 0.30 * f.recent_score_movement + 0.20 * f.momentum_swing + 0.10 * f.competitive_history)
    raw = 0.50 * competitiveness + 0.15 * game_quality + 0.15 * f.team_quality + 0.10 * f.stakes + 0.10 * drama
    calibrated = calibrate(raw, competitiveness)

    margin = f.margin_competitiveness; uncertainty = f.outcome_uncertainty
    points = state.get("home_score", 0) + state.get("away_score", 0)
    score_diff = abs(state.get("home_score", 0) - state.get("away_score", 0))
    # Keep weak-team, low-uncertainty blowouts low without applying the same
    # ceiling to elite matchups where the fixture contract permits a higher floor.
    if score_diff >= 30 and uncertainty < 10: calibrated = min(calibrated, 15.0)
    elif score_diff >= 25 and uncertainty < 10 and f.team_quality < 70: calibrated = min(calibrated, 15.0)
    elif margin < 35 and uncertainty < 10 and f.late_game_pressure > 50: calibrated = min(calibrated, 30.0)
    elif margin < 35 and uncertainty < 25 and f.late_game_pressure > 50: calibrated = min(calibrated, 35.0)
    if score_diff >= 14 and state.get("quarter", 1) <= 2: calibrated = min(calibrated, 55.0)
    if points <= 3 and f.late_game_pressure > 50: calibrated = min(calibrated, 70.0)
    if points <= 25 and competitiveness < 90 and f.late_game_pressure > 50: calibrated = min(calibrated, 95.0)

    if state.get("down") == 4 and state.get("field_position_yards_to_goal") is not None and state.get("field_position_yards_to_goal") <= 5 and state.get("seconds_remaining", 3600) <= 30:
        calibrated = clamp(calibrated + 2.0)
    if state.get("quarter", 1) >= 5:
        # Overtime raises leverage without making every OT state a 100.
        calibrated = clamp(calibrated + 2.0)
    if context.get("game_stage") in {"SUPER_BOWL", "NCAA_NATIONAL_CHAMPIONSHIP"} and competitiveness >= 70: calibrated = clamp(calibrated + 1.5)

    return {"competitiveness": clamp(competitiveness), "game_quality": clamp(game_quality), "team_quality": clamp(f.team_quality), "stakes": clamp(f.stakes), "drama": clamp(drama), "raw_score": clamp(raw), "game_score": round(clamp(calibrated), 2)}
