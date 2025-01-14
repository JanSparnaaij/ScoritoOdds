from app.celery_worker import celery
from app.tennis_fetcher import fetch_combined_tennis_data
from app.football_fetcher import fetch_all_matches_async
from flask import Flask
from app import cache
import asyncio
import logging

logger = logging.getLogger(__name__)

def get_app_context():
    """Create and return a Flask app instance."""
    from app import create_app
    return create_app()

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
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
            matches = fetch_combined_tennis_data(matches_url, rounds_url)
            cache.set(f"tennis_matches_{league}", matches, timeout=3600)
            logger.info(f"Tennis data for {league} successfully cached.")
        except Exception as e:
            logger.error(f"Error fetching tennis data for {league}: {e}")


@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    app = get_app_context()
    with app.app_context():
        from app.constants import LEAGUES
        url = LEAGUES.get(league, LEAGUES["eredivisie"])
        logger.info(f"Fetching football matches for league: {league} with URL: {url}")

        try:
            loop = asyncio.get_event_loop()
            matches = loop.run_until_complete(fetch_all_matches_async(url))
            cache.set(f"matches_{league}", matches, timeout=3600)
            logger.info(f"Football data for {league} successfully cached.")
        except Exception as e:
            logger.error(f"Error fetching football data for {league}: {e}")
