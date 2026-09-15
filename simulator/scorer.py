from __future__ import annotations
from .features import FeatureSnapshot, clamp

MODEL_VERSION = "football-lab-v1"

def score_features(f: FeatureSnapshot) -> dict[str, float]:
    margin_state = 0.65*f.margin_competitiveness + 0.35*f.competitive_state
    competitiveness = (0.45*f.outcome_uncertainty + 0.25*(f.late_game_pressure*(0.35+0.65*f.outcome_uncertainty/100)) + 0.20*margin_state + 0.10*f.competitive_history)
    game_quality = 0.30*f.scoring_action + 0.25*f.explosive_play_rate + 0.25*f.high_leverage_event_rate + 0.20*f.performance_quality
    drama = clamp(0.50*f.wp_volatility + 0.30*f.recent_score_movement + 0.20*f.momentum_swing)
    raw = 0.50*competitiveness + 0.15*game_quality + 0.15*f.team_quality + 0.10*f.stakes + 0.10*drama
    if f.outcome_uncertainty < 25 and f.margin_competitiveness < 20: raw=min(raw,20)
    elif f.outcome_uncertainty < 40 and f.margin_competitiveness < 35: raw=min(raw,45)
    return {"competitiveness":clamp(competitiveness),"game_quality":clamp(game_quality),"team_quality":clamp(f.team_quality),"stakes":clamp(f.stakes),"drama":drama,"raw_score":clamp(raw),"game_score":round(clamp(raw),2)}
