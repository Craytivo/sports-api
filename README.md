# Sports API

Football Game Score V1 with a frozen scoring contract and provider-neutral production integration.

## Current scope

- NFL + NCAA Football
- Frozen Football Game Score V1 reference model
- Provider-neutral `CanonicalGame` contract
- ESPN scoreboard adapter for live/pregame/final game state

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
  -> production.score_game()
  -> Game Score + feature/component breakdown
```

The provider boundary is defined in `production/provider.py`. Provider-specific parsing belongs in `production/providers/`; scoring consumes only `CanonicalGame`.

### ESPN provider

`production.providers.ESPNProvider` supports:

- `NFL`
- `NCAA_FOOTBALL`

Example:

```python
from production.ingestion import GameIngestion
from production.providers import ESPNProvider

provider = ESPNProvider()
ingestion = GameIngestion(provider)
games = ingestion.fetch_games("NFL")
```

The ESPN adapter currently supplies scoreboard/game-state data. Team strength remains the canonical neutral baseline (`50.0`) until a separate ratings source is integrated; it is intentionally not inferred from provider rank.

## Architecture rule

Provider-specific fields, endpoint formats, IDs, and status codes must stop at the adapter boundary. The production scoring engine must remain provider-agnostic.

> `simulator/` is the behavioral lab/reference implementation. `production/` is the integration layer.
