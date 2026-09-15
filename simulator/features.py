from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any

def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))

def late_pressure(seconds_remaining: int, quarter: int) -> float:
    if quarter >= 5: return 100.0
    ratio = clamp(seconds_remaining / 3600.0, 0.0, 1.0)
    return 100.0 * (1.0 - ratio) ** 2

def margin_competitiveness(diff: int) -> float:
    return 100.0 * math.exp(-0.08 * abs(diff))

def close_duration_score(history: dict[str, Any], elapsed_seconds: int) -> float:
    if elapsed_seconds <= 0: return 0.0
    return clamp(100.0 * history.get("close_game_seconds", 0) / elapsed_seconds)

def count_score(n: int) -> float: return clamp(25.0 * n)

def competitive_history(history: dict[str, Any]) -> float:
    return (0.30 * count_score(history.get("lead_changes", 0)) + 0.20 * count_score(history.get("ties", 0)) + 0.30 * close_duration_score(history, history.get("elapsed_seconds", 1800)) + 0.20 * count_score(history.get("comeback_events", 0)))

def synthetic_wp(state: dict[str, Any], teams: dict[str, Any]) -> float:
    if "home_win_probability" in state: return float(state["home_win_probability"])
    diff = state.get("home_score", 0) - state.get("away_score", 0)
    remaining = state.get("seconds_remaining", 3600)
    urgency = 1.0 + 3.0 * (1.0 - clamp(remaining / 3600.0))
    strength = (teams.get("home_strength", 50) - teams.get("away_strength", 50)) / 25.0
    x = 0.28 * diff * urgency + strength
    if state.get("possession") == "HOME": x += 0.8
    elif state.get("possession") == "AWAY": x -= 0.8
    field = state.get("field_position_yards_to_goal")
    if field is not None: x += (100 - field) / 80.0 if state.get("possession") == "HOME" else -(100 - field) / 80.0
    return 1.0 / (1.0 + math.exp(-x))

def scoring_action(state: dict[str, Any], events: list[dict[str, Any]]) -> float:
    points = state.get("home_score", 0) + state.get("away_score", 0)
    recent = sum(e.get("points", 0) for e in events[-5:])
    return clamp(25 + points * 0.75 + recent * 1.5)

def explosive_play_rate(events: list[dict[str, Any]]) -> float:
    plays = [e for e in events if e.get("type") in {"play", "explosive_play", "pass", "rush"}]
    if not plays: return 50.0
    explosive = sum(1 for e in plays if e.get("explosive", False) or e.get("type") == "explosive_play")
    return clamp(100.0 * explosive / len(plays))

def high_leverage_event_rate(events: list[dict[str, Any]]) -> float:
    if not events: return 20.0
    weights = {"turnover": 2.0, "fourth_down": 1.5, "touchdown": 1.3, "game_tying_score": 2.0, "go_ahead_score": 2.0}
    return clamp(sum(weights.get(e.get("type"), 0.25) for e in events) * 8.0)

def performance_quality(state: dict[str, Any], teams: dict[str, Any]) -> float:
    avg = (teams.get("home_strength", 50) + teams.get("away_strength", 50)) / 2
    return clamp(45 + 0.35 * (avg - 50) + min(state.get("home_score", 0) + state.get("away_score", 0), 50) * 0.2)

def competitive_state(state: dict[str, Any]) -> float:
    remaining = state.get("seconds_remaining", 3600); late = late_pressure(remaining, state.get("quarter", 1))
    diff = abs(state.get("home_score", 0) - state.get("away_score", 0)); margin = margin_competitiveness(diff)
    leverage = late * (0.65 + 0.35 * margin / 100.0); threat = 0.0
    field = state.get("field_position_yards_to_goal")
    if field is not None and state.get("possession") in {"HOME", "AWAY"}: threat = 100.0 - field
    if state.get("down") == 4: leverage = clamp(leverage + 20)
    if field is not None and field <= 20: leverage = clamp(leverage + 15)
    return clamp(0.40 * leverage + 0.30 * late + 0.20 * threat + 0.10 * (100 if state.get("possession") != "UNKNOWN" else 25))

@dataclass(frozen=True)
class FeatureSnapshot:
    outcome_uncertainty: float; late_game_pressure: float; margin_competitiveness: float; competitive_state: float; competitive_history: float
    scoring_action: float; explosive_play_rate: float; high_leverage_event_rate: float; performance_quality: float
    team_quality: float; stakes: float; wp_volatility: float; recent_score_movement: float; momentum_swing: float
    def as_dict(self) -> dict[str, float]: return self.__dict__.copy()

def calculate_features(scenario: dict[str, Any]) -> FeatureSnapshot:
    state=scenario.get("game_state",{}); teams=scenario.get("teams",{}); context=scenario.get("context",{}); history=scenario.get("history",{}); events=scenario.get("events",[])
    wp=synthetic_wp(state,teams); uncertainty=clamp(100*(1-2*abs(wp-.5))); margin=margin_competitiveness(state.get("home_score",0)-state.get("away_score",0)); late=late_pressure(state.get("seconds_remaining",3600),state.get("quarter",1)); history_score=competitive_history(history)
    avg=(teams.get("home_strength",50)+teams.get("away_strength",50))/2; balance=100-abs(teams.get("home_strength",50)-teams.get("away_strength",50)); team_quality=clamp(.70*avg+.30*balance)
    stage={"PRESEASON":15,"REGULAR_SEASON":35,"WILD_CARD":75,"DIVISIONAL":85,"CONFERENCE_CHAMPIONSHIP":95,"SUPER_BOWL":100,"NCAA_REGULAR_SEASON":35,"NCAA_CONFERENCE_CHAMPIONSHIP":75,"NCAA_PLAYOFF":90,"NCAA_NATIONAL_CHAMPIONSHIP":100}
    impact={"NONE":0,"LOW":25,"MEDIUM":55,"HIGH":100,"UNKNOWN":35}; rivalry={"NONE":0,"NOTABLE":50,"MAJOR":100}
    stakes=clamp(.40*stage.get(context.get("game_stage","REGULAR_SEASON"),35)+.40*impact.get(context.get("playoff_impact","UNKNOWN"),35)+.15*rivalry.get(context.get("rivalry","NONE"),0)+.05*(100 if context.get("historical_context") not in {None,"NONE"} else 0))
    wp_vol=clamp(sum(abs(e.get("wp_change",0)) for e in events)*100); recent=clamp(sum(e.get("points",0) for e in events[-3:])*8); momentum=clamp(wp_vol*.6+recent*.4)
    return FeatureSnapshot(uncertainty,late,margin,competitive_state(state),history_score,scoring_action(state,events),explosive_play_rate(events),high_leverage_event_rate(events),performance_quality(state,teams),team_quality,stakes,wp_vol,recent,momentum)
