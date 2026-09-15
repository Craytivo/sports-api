from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Any

from .features import calculate_features
from .scorer import score_features

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "football_anchors_v1.json"


def main() -> int:
    scenarios = {s["id"]: s for s in json.loads(FIXTURES.read_text(encoding="utf-8"))["scenarios"]}
    base = scenarios["NFL-LIVE-C01"]
    rows = []
    for quarter, seconds in [(1,900),(2,660),(3,900),(4,600),(4,300),(4,120),(4,30)]:
        scenario = copy.deepcopy(base)
        scenario["game_state"]["quarter"] = quarter
        scenario["game_state"]["seconds_remaining"] = seconds
        features = calculate_features(scenario)
        components = score_features(features)
        rows.append({"quarter": quarter, "seconds_remaining": seconds, "score": components["game_score"], "features": features.as_dict(), "components": components})
    out = ROOT / "sweep-report.json"
    out.write_text(json.dumps({"model_version":"football-lab-v1","late_pressure_tied":rows}, indent=2), encoding="utf-8")
    for row in rows:
        print(f"Q{row['quarter']} {row['seconds_remaining']:4}s -> {row['score']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
