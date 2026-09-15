from production.ingestion import GameIngestion
from production.models import CanonicalGame
from production.providers import ESPNProvider
from production.scoring import score_game


def _espn_event() -> dict:
    return {
        "id": "test-espn-1",
        "season": {"slug": "2026-regular-season"},
        "competitions": [
            {
                "competitors": [
                    {
                        "id": "1",
                        "homeAway": "home",
                        "score": "24",
                        "team": {"id": "1", "displayName": "Home Team"},
                    },
                    {
                        "id": "2",
                        "homeAway": "away",
                        "score": "21",
                        "team": {"id": "2", "displayName": "Away Team"},
                    },
                ],
                "status": {
                    "period": 4,
                    "displayClock": "2:30",
                    "type": {"name": "STATUS_IN_PROGRESS", "completed": False},
                },
            }
        ],
    }


def test_espn_adapter_returns_canonical_game_without_provider_fields():
    provider = ESPNProvider()
    game = provider._game_from_event(_espn_event(), "NFL", "2026-09-15T00:00:00+00:00")

    assert isinstance(game, CanonicalGame)
    assert game.source == "espn"
    assert game.home.name == "Home Team"
    assert game.away.name == "Away Team"
    assert game.state.home_score == 24
    assert game.state.away_score == 21
    assert game.state.quarter == 4
    assert game.state.seconds_remaining == 150
    assert not hasattr(game, "competitors")


def test_ingestion_and_scoring_use_only_canonical_contract():
    provider = ESPNProvider()
    ingestion = GameIngestion(provider)

    class StubProvider:
        name = "stub"

        def fetch_games(self, sport, *, date=None):
            return [provider._game_from_event(_espn_event(), sport, "2026-09-15T00:00:00+00:00")]

    games = GameIngestion(StubProvider()).fetch_games("NFL")
    result = score_game(games[0])

    assert result["game_id"] == "test-espn-1"
    assert 0 <= result["game_score"] <= 100
    assert result["model_version"]
