from app.celery_worker import celery
from app.tennis_fetcher import fetch_combined_tennis_data
from app.football_fetcher import fetch_all_matches_async
from app import cache, create_app
import asyncio
import logging
import sys
import os
import warnings

# Ensure the root directory is included in PYTHONPATH
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
print("Current PYTHONPATH:", sys.path)

logger = logging.getLogger(__name__)

app = create_app()  # Create the Flask app instance


@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
    with app.app_context():
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


# football task
@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    with app.app_context():
        from app.routes import LEAGUES
        url = LEAGUES.get(league, LEAGUES['eredivisie'])
        logger.info(f"Fetching football matches for league: {league} with URL: {url}")

        try:
            # Use asyncio.run to execute the coroutine
            matches = asyncio.run(fetch_all_matches_async(url))
            cache.set(f"matches_{league}", matches, timeout=3600)
            logger.info(f"Football data for {league} successfully cached.")
        except Exception as e:
            logger.error(f"Error fetching football data for {league}: {e}")

warnings.filterwarnings("ignore", category=UserWarning)
