from __future__ import annotations

from production.providers import ESPNProvider
from production.ratings import ESPNPowerIndexRatingsProvider


def main() -> None:
    games_provider = ESPNProvider(timeout_seconds=15)
    ratings_provider = ESPNPowerIndexRatingsProvider(timeout_seconds=15)

    for sport in ("NFL", "NCAA_FOOTBALL"):
        games = games_provider.fetch_games(sport)
        assert isinstance(games, list)
        print(f"{sport}: {len(games)} ESPN events")
        for game in games[:3]:
            print(
                f"  {game.id}: {game.away.name} @ {game.home.name} "
                f"{game.phase} {game.state.away_score}-{game.state.home_score} "
                f"Q{game.state.quarter} {game.state.seconds_remaining}s"
            )
        ratings = ratings_provider.fetch_ratings(sport)
        print(f"{sport}: {len(ratings)} ESPN Power Index ratings")
        if ratings:
            values = [rating.strength for rating in ratings.values()]
            assert min(values) >= 0.0
            assert max(values) <= 100.0

    print("ESPN live validation: PASS")


if __name__ == "__main__":
    main()
