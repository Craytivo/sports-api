# Sports API

Football Game Score V1 synthetic scoring simulator and regression harness.

## Current scope

- NFL + NCAA Football
- Synthetic scenarios only
- Reference scoring model for validation before production scoring integration

## Run

```bash
python -m simulator.run_regression
```

The harness reads `tests/fixtures/football_anchors_v1.json`, calculates normalized football features, runs the reference Game Score model, evaluates absolute ranges, pairwise assertions, guardrails, event responses, and emits a machine-readable report.

> The reference scorer is intentionally isolated from future production scoring code. It is a lab/reference implementation, not the production engine.
