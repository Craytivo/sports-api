# Football Scoring Simulator & Regression Harness V1

This is the pre-production lab for the Football Game Score model.

```text
fixtures
  -> synthetic scenario generator
  -> football feature calculator
  -> lab/reference scorer
  -> regression assertions
  -> JSON report
```

The reference scorer is intentionally isolated in `simulator/scorer.py`. It exists to make the anchor suite executable now; it is not the production scoring engine.

## Run

```bash
python -m simulator.run_regression
```

The command writes `regression-report.json` and exits `0` only when the complete suite passes.

## Tested

- absolute score ranges
- pairwise rankings
- blowout ceilings
- team-quality guardrails
- rivalry guardrails
- NFL/NCAA coverage
- pregame/live/final states

`simulator/generator.py` provides deterministic helpers for clock and event variants without mutating canonical fixtures.

## Important

The current lab scorer is deliberately provisional. A failing anchor is useful: it means the feature/scoring assumptions do not yet satisfy the product contract. Do not weaken an anchor to make the suite green. Adjust the model, document the reason, and rerun the suite.
