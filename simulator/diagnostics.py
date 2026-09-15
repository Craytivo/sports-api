from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from .features import calculate_features
from .scorer import MODEL_VERSION, score_features

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "football_anchors_v1.json"


def load_scenarios(path: Path = FIXTURES) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))["scenarios"]


def explain(scenario: dict[str, Any]) -> dict[str, Any]:
    features = calculate_features(scenario)
    components = score_features(features, scenario.get("game_state"), scenario.get("context"), scenario.get("phase"))
    return {"scenario_id": scenario["id"], "name": scenario["name"], "score": components["game_score"], "features": features.as_dict(), "components": components}


def score_curve(base: dict[str, Any], clocks: list[int]) -> list[dict[str, float]]:
    rows = []
    for seconds_remaining in clocks:
        scenario = json.loads(json.dumps(base))
        scenario["game_state"]["seconds_remaining"] = seconds_remaining
        scenario["game_state"]["quarter"] = 4
        result = explain(scenario)
        rows.append({"seconds_remaining": seconds_remaining, "score": result["score"]})
    return rows


def main() -> int:
    scenarios = load_scenarios()
    report = {"model_version": MODEL_VERSION, "anchor_diagnostics": [explain(s) for s in scenarios], "late_game_curve": score_curve(next(s for s in scenarios if s["id"] == "NFL-LIVE-C01"), [900, 600, 480, 300, 180, 120, 60, 30, 0])}
    out = ROOT / "diagnostic-report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Football scoring diagnostics")
    for row in report["anchor_diagnostics"]:
        c = row["components"]
        print(f"{row['scenario_id']:18} score={row['score']:6.2f} comp={c['competitiveness']:6.2f} quality={c['game_quality']:6.2f} team={c['team_quality']:6.2f} stakes={c['stakes']:6.2f} drama={c['drama']:6.2f}")
    print("Late-game score curve")
    for row in report["late_game_curve"]: print(f"  {row['seconds_remaining']:4}s -> {row['score']:6.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
