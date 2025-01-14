from app.celery_worker import celery
from app.tennis_fetcher import fetch_combined_tennis_data
from app.football_fetcher import fetch_all_matches_async
from app import cache
import asyncio
import logging

logger = logging.getLogger(__name__)

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
    """
    Fetch tennis matches in the background and cache them.
    """
    from app.routes import TENNIS_LEAGUES  # Local import to avoid circular dependencies
    league_urls = TENNIS_LEAGUES.get(league, {})
    matches_url = league_urls.get("matches")
    rounds_url = league_urls.get("rounds")

    logger.info(f"Fetching tennis matches for league: {league} with matches URL: {matches_url} and rounds URL: {rounds_url}")
    try:
        matches = fetch_combined_tennis_data(matches_url, rounds_url)
        logger.info(f"Fetched tennis matches: {matches}")
        cache.set(f"tennis_matches_{league}", matches, timeout=3600)
        logger.info(f"Tennis data for {league} successfully cached.")
        return matches
    except Exception as e:
        logger.error(f"Error fetching tennis data for {league}: {e}")
        return None


@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    """
    Fetch football matches in the background and cache them.
    """
    from app.routes import LEAGUES  # Local import to avoid circular dependencies
    url = LEAGUES.get(league, LEAGUES['eredivisie'])
    logger.info(f"Fetching football matches for league: {league} with URL: {url}")
    try:
        matches = asyncio.run(fetch_all_matches_async(url))
        logger.info(f"Fetched football matches: {matches}")
        cache.set(f"matches_{league}", matches, timeout=3600)
        logger.info(f"Football data for {league} successfully cached.")
        return matches
    except Exception as e:
        logger.error(f"Error fetching football data for {league}: {e}")
        return None
