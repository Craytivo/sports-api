from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
from .features import calculate_features
from .scorer import MODEL_VERSION, score_features

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = ROOT / "tests" / "fixtures" / "football_anchors_v1.json"


def _pairwise_tests(ids: set[str]):
    pairs = [
        ("PAIR-001", "NFL-LIVE-C01", "NFL-LIVE-D01", "Late close must outrank early close"),
        ("PAIR-002", "NFL-LIVE-F01", "NFL-LIVE-E01", "Late one-score must outrank early one-score"),
        ("PAIR-003", "NFL-LIVE-J01", "NFL-LIVE-K01", "Weak-team thriller must outrank elite blowout"),
        ("PAIR-004", "NFL-LIVE-N01", "NFL-LIVE-O01", "Competitive defensive thriller must beat noncompetitive shootout"),
        ("PAIR-005", "NFL-LIVE-W01", "NFL-LIVE-V01", "Real comeback path must beat dead state"),
        ("PAIR-006", "NFL-LIVE-I01", "NFL-LIVE-K01", "Blowout must not outrank extraordinary thriller"),
        ("PAIR-007", "NFL-LIVE-H01", "NFL-LIVE-D01", "Low-probability comeback should rank below live one-score game"),
        ("PAIR-008", "NFL-LIVE-Y01", "NFL-LIVE-X01", "Fourth-down leverage must matter"),
    ]
    return [
        {"id": i, "a": a, "b": b, "relation": ">", "reason": r, "severity": "CRITICAL"}
        for i, a, b, r in pairs
        if a in ids and b in ids
    ]


def _guardrails(ids: set[str]):
    checks = [
        ("GR-001", "NFL-LIVE-I01", 20, "Massive blowout ceiling"),
        ("GR-002", "NFL-LIVE-J01", 45, "Elite team quality cannot rescue blowout"),
        ("GR-003", "NFL-LIVE-L01", 20, "Weak-team blowout remains low"),
        ("GR-004", "NCAA-LIVE-Z01", 30, "Rivalry cannot rescue blowout"),
        ("GR-005", "NCAA-LIVE-AC01", 20, "NCAA ranked blowout remains low"),
    ]
    return [
        {"id": i, "scenario": s, "assert": "score <= max", "max": m, "reason": r, "severity": "CRITICAL"}
        for i, s, m, r in checks
        if s in ids
    ]


def run_scenarios(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for s in scenarios:
        features = calculate_features(s)
        components = score_features(features, s.get("game_state"), s.get("context"))
        exp = s.get("expected", {})
        lo, hi = exp.get("score_min"), exp.get("score_max")
        ok = lo is None or hi is None or lo <= components["game_score"] <= hi
        results.append({
            "scenario_id": s["id"],
            "name": s["name"],
            "score": components["game_score"],
            "expected": {"min": lo, "max": hi},
            "absolute_pass": ok,
            "features": features.as_dict(),
            "components": components,
        })

    by_id = {r["scenario_id"]: r for r in results}
    tests = []
    for t in _pairwise_tests(set(by_id)):
        a, b = by_id[t["a"]], by_id[t["b"]]
        passed = a["score"] > b["score"]
        tests.append({**t, "actual": {"a": a["score"], "b": b["score"]}, "pass": passed})

    for t in _guardrails(set(by_id)):
        r = by_id[t["scenario"]]
        tests.append({**t, "actual": r["score"], "pass": r["score"] <= t["max"]})

    abs_fail = [r for r in results if not r["absolute_pass"]]
    test_fail = [t for t in tests if not t["pass"]]
    total = len(results) + len(tests)
    passed = total - len(abs_fail) - len(test_fail)

    return {
        "model_version": MODEL_VERSION,
        "scenario_suite": "anchors-v1",
        "summary": {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "critical_failures": sum(t["severity"] == "CRITICAL" for t in test_fail),
            "status": "PASS" if not abs_fail and not test_fail else "FAIL",
        },
        "scenario_results": results,
        "regression_tests": tests,
        "failures": [{"type": "absolute", **r} for r in abs_fail] + test_fail,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    p.add_argument("--report", default="regression-report.json")
    args = p.parse_args()
    data = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
    report = run_scenarios(data["scenarios"])
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Football scoring regression: {report['summary']['status']}")
    print(f"Tests: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
    for f in report["failures"]:
        print(f"  - {f.get('id', f.get('scenario_id'))}: {f.get('reason', f.get('name', 'absolute range'))}")
    return 0 if report["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
