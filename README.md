# Sports API

Football Game Score V1 with a frozen scoring contract and provider-neutral production integration.

## Current scope

- NFL + NCAA Football
- Frozen Football Game Score V1 reference model
- Provider-neutral `CanonicalGame` contract
- ESPN scoreboard adapter for live/pregame/final game state
- Optional ESPN Power Index team-strength integration

## Regression harness

```bash
python -m simulator.runner
```

The harness reads `tests/fixtures/football_anchors_v1.json`, calculates normalized football features, runs the reference Game Score model, evaluates absolute ranges, pairwise assertions, guardrails, event responses, and emits a machine-readable report.

The scoring model is frozen after the V1 regression suite passed 47/47. Production integration must preserve that behavioral contract; provider integration must not modify scoring weights or formulas.

## Production flow

```text
provider
  -> SportsProvider
  -> CanonicalGame
  -> optional TeamRatingsProvider
  -> production.score_game()
  -> Game Score + feature/component breakdown
```

The provider boundary is defined in `production/provider.py`. Provider-specific parsing belongs in `production/providers/`; scoring consumes only `CanonicalGame`.

### ESPN provider

`production.providers.ESPNProvider` supports:

- `NFL`
- `NCAA_FOOTBALL`
- score, clock, quarter, possession, down, distance, field position, timeouts, and available win probability from ESPN's scoreboard situation payload

Example:

```python
from production.ingestion import GameIngestion
from production.providers import ESPNProvider
from production.ratings import ESPNPowerIndexRatingsProvider

provider = ESPNProvider()
ratings = ESPNPowerIndexRatingsProvider()
ingestion = GameIngestion(provider, ratings)
games = ingestion.fetch_games("NFL", season=2026)
```

### Team strength / ratings

`production.ratings.ESPNPowerIndexRatingsProvider` reads ESPN's season Power Index endpoint and normalizes the returned team ratings to the canonical `0-100` strength field. This is an input-data transformation only; it does not change the frozen scoring formulas, weights, calibration, or model version.

If a team is missing from the external ratings response, its existing canonical strength is preserved (`50.0` by default).

### Live feed validation

Run against the real ESPN endpoints with:

```bash
python scripts/validate_espn_live.py
```

The validator checks both NFL and NCAA Football scoreboard feeds, canonicalizes returned events, and validates the ESPN Power Index ratings range.

## Architecture rule

Provider-specific fields, endpoint formats, IDs, and status codes must stop at the adapter boundary. The production scoring engine must remain provider-agnostic.

> `simulator/` is the behavioral lab/reference implementation. `production/` is the integration layer.
