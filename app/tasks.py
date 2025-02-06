from app.celery_worker import celery
from app.utils import fetch_matches_and_cache, log_task_status
from app.constants import TENNIS_LEAGUES, LEAGUES
from app.fetchers import fetch_football_matches_async, fetch_combined_tennis_data
from app.browser import close_browser, get_browser
import logging
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # Ensure current dir is in path
sys.path.append("/app/app")  # Add /app/app explicitly

from browser import close_browser, get_browser
logger = logging.getLogger(__name__)

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league: str) -> None:
    """
    Fetch and process tennis matches for a specific league.
    """
    from flask import current_app

    try:
        log_task_status(logger, "start", task_name="fetch_tennis_matches_in_background", league=league)

        league_urls = TENNIS_LEAGUES.get(league, {})
        matches_url = league_urls.get("matches")
        rounds_url = league_urls.get("rounds")

        if not matches_url:
            logger.warning(f"Invalid tennis league: {league}")
            return

        async def task_logic():
            # Use a fresh browser instance for this task
            browser = await get_browser(current_app)
            try:
                await fetch_matches_and_cache(
                    fetch_func=fetch_combined_tennis_data,
                    cache_key=f"tennis_matches_{league}",
                    fetch_args=(matches_url, rounds_url),
                    logger=logger,
                )
            finally:
                await close_browser(current_app)

        asyncio.run(task_logic())

    except Exception as e:
        logger.error(f"Error in fetch_tennis_matches_in_background for league {league}: {e}")

@celery.task(name="app.tasks.fetch_football_in_background")
def fetch_football_in_background(league: str) -> None:
    """
    Fetch and process football matches for a specific league.

    Args:
        league (str): League name as defined in LEAGUES.
    """
    from flask import current_app

    try:
        log_task_status(logger, "start", task_name="fetch_football_in_background", league=league)

        league_url = LEAGUES.get(league)
        if not league_url:
            logger.warning(f"Invalid football league: {league}")
            return

        async def task_logic():
            # Use a fresh browser instance for each task
            browser = await get_browser(current_app)
            try:
                await fetch_matches_and_cache(
                    fetch_func=fetch_football_matches_async,
                    cache_key=f"matches_{league}",
                    fetch_args=(league_url,),
                    logger=logger,
                )
            finally:
                await close_browser(current_app)

        # Run the async task logic
        asyncio.run(task_logic())
    except Exception as e:
        logger.error(f"Error in fetch_football_in_background for league {league}: {e}")

@celery.task(name="app.tasks.test_task")
def test_task() -> str:
    """
    A simple test task to validate the setup.

    Returns:
        str: Success message.
    """
    logger.info("Test task executed successfully.")
    return "Success"
