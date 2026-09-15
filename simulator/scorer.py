from __future__ import annotations
from .features import FeatureSnapshot, clamp

MODEL_VERSION = "football-lab-v1.1"

def calibrate(raw: float) -> float:
    if raw <= 0:
        return 0.0
    return clamp(100.0 * (raw / 100.0) ** 0.35)

def score_features(f: FeatureSnapshot) -> dict[str, float]:
    margin_state = 0.55 * f.margin_competitiveness + 0.45 * f.competitive_state
    competitiveness = (0.45 * f.outcome_uncertainty + 0.25 * (f.late_game_pressure * (0.35 + 0.65 * f.outcome_uncertainty / 100.0)) + 0.20 * margin_state + 0.10 * f.competitive_history)
    game_quality = 0.30 * f.scoring_action + 0.25 * f.explosive_play_rate + 0.25 * f.high_leverage_event_rate + 0.20 * f.performance_quality
    drama = clamp(0.50 * f.wp_volatility + 0.30 * f.recent_score_movement + 0.20 * f.momentum_swing + 0.10 * f.competitive_history)
    raw = 0.50 * competitiveness + 0.15 * game_quality + 0.15 * f.team_quality + 0.10 * f.stakes + 0.10 * drama
    margin = f.margin_competitiveness
    uncertainty = f.outcome_uncertainty
    calibrated = calibrate(raw)
    if margin < 20 and uncertainty < 10:
        calibrated = min(calibrated, 15.0)
    elif margin < 35 and uncertainty < 10 and f.late_game_pressure > 50:
        calibrated = min(calibrated, 30.0)
    elif margin < 35 and uncertainty < 25 and f.late_game_pressure > 50:
        calibrated = min(calibrated, 45.0)
    return {"competitiveness": clamp(competitiveness), "game_quality": clamp(game_quality), "team_quality": clamp(f.team_quality), "stakes": clamp(f.stakes), "drama": clamp(drama), "raw_score": clamp(raw), "game_score": round(clamp(calibrated), 2)}
