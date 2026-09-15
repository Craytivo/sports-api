import json
from pathlib import Path
from simulator.runner import run_scenarios

def test_anchor_suite_is_executable():
    path = Path(__file__).parent / "fixtures" / "football_anchors_v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    report = run_scenarios(data["scenarios"])
    assert report["scenario_suite"] == "anchors-v1"
    assert report["summary"]["total_tests"] > len(data["scenarios"])
    assert len(report["scenario_results"]) == len(data["scenarios"])
    assert "failures" in report
