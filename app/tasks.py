from app.celery_worker import celery
from app.tennis_fetcher import fetch_combined_tennis_data
from app.football_fetcher import fetch_all_matches_async
from app import cache
import asyncio
import logging

logger = logging.getLogger(__name__)

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
    from app.routes import TENNIS_LEAGUES
    league_urls = TENNIS_LEAGUES.get(league, {})
    matches_url = league_urls.get("matches")
    rounds_url = league_urls.get("rounds")

    try:
        matches = fetch_combined_tennis_data(matches_url, rounds_url)
        cache.set(f"tennis_matches_{league}", matches, timeout=3600)
        logger.info(f"Tennis data for {league} successfully cached.")
    except Exception as e:
        logger.error(f"Error fetching tennis data for {league}: {e}")

@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    from app.routes import LEAGUES
    league_url = LEAGUES.get(league)
    try:
        matches = asyncio.run(fetch_all_matches_async(league_url))
        cache.set(f"matches_{league}", matches, timeout=3600)
        logger.info(f"Football data for {league} successfully cached.")
    except Exception as e:
        logger.error(f"Error fetching football data for {league}: {e}")
