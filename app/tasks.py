from app.celery_worker import celery
from app.tennis_fetcher import fetch_combined_tennis_data
from app.football_fetcher import fetch_all_matches_async
from flask import Flask
import asyncio
import logging
import json
import sys
import os

logger = logging.getLogger(__name__)


def get_app_context():
    """Create and return a Flask app instance."""
    # Ensure the base directory is in the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(project_root, ".."))

    from app import create_app
    return create_app()


@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
    """Fetch and store tennis matches for a specific league."""
    app = get_app_context()
    with app.app_context():
        from app.constants import TENNIS_LEAGUES

        league_urls = TENNIS_LEAGUES.get(league, {})
        matches_url = league_urls.get("matches")
        rounds_url = league_urls.get("rounds")

        if not matches_url:
            logger.warning(f"Invalid league: {league}")
            return

        try:
            # Fetch and format matches
            matches = fetch_combined_tennis_data(matches_url, rounds_url)
            formatted_matches = [
                {
                    "date": match["date"],
                    "round": match["round"],
                    "players": match["players"],
                    "categories": match["categories"],
                    "odds": match["odds"],
                    "expected_points": match["expected_points"]
                }
                for match in matches
            ]

            # Store in Redis
            app.redis_client.set(f"tennis_matches_{league}", json.dumps(formatted_matches), ex=3600)
            logger.info(f"Tennis data for {league} successfully cached.")
        except Exception as e:
            logger.error(f"Error fetching tennis data for {league}: {e}")


@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    """Fetch and store football matches for a specific league."""
    app = get_app_context()
    with app.app_context():
        from app.constants import LEAGUES

        url = LEAGUES.get(league, LEAGUES["eredivisie"])
        app.logger.info(f"Fetching football matches for league: {league} with URL: {url}")

        try:
            # Fetch matches
            loop = asyncio.get_event_loop()
            matches = loop.run_until_complete(fetch_all_matches_async(url))

            # Format matches for Redis
            formatted_matches = [
                {
                    "home_team": match["home_team"],
                    "away_team": match["away_team"],
                    "odds": {
                        "home": match["odds"]["home"],
                        "draw": match["odds"]["draw"],
                        "away": match["odds"]["away"]
                    }
                }
                for match in matches
            ]

            # Log matches to ensure correctness
            app.logger.info(f"Matches retrieved: {formatted_matches}")

            # Store in Redis
            app.redis_client.set(f"matches_{league}", json.dumps(formatted_matches), ex=3600)
            app.logger.info(f"Football data for {league} successfully cached.")
        except Exception as e:
            logger.error(f"Error fetching football data for {league}: {e}")
