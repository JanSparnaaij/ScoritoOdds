from app.celery_worker import celery
from app.utils import fetch_matches_and_cache, log_task_status
from app.constants import TENNIS_LEAGUES, LEAGUES
from app.fetchers import fetch_football_matches_async, fetch_combined_tennis_data
from app.processors import process_tennis_matches, process_football_matches
import logging
import nest_asyncio
import asyncio

logger = logging.getLogger(__name__)

# Patch the event loop to allow nested async calls
nest_asyncio.apply()

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league: str) -> None:
    """
    Fetch and process tennis matches for a specific league.

    Args:
        league (str): League name as defined in TENNIS_LEAGUES.
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

        # Ensure the event loop is properly managed
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Use `create_task` if already in an event loop (like Celery)
            task = loop.create_task(
                fetch_matches_and_cache(
                    fetch_func=fetch_combined_tennis_data,
                    cache_key=f"tennis_matches_{league}",
                    fetch_args=(matches_url, rounds_url),
                    logger=logger,
                    process_func=process_tennis_matches,
                )
            )
            loop.run_until_complete(task)
        else:
            asyncio.run(
                fetch_matches_and_cache(
                    fetch_func=fetch_combined_tennis_data,
                    cache_key=f"tennis_matches_{league}",
                    fetch_args=(matches_url, rounds_url),
                    logger=logger,
                    process_func=process_tennis_matches,
                )
            )
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

        # Ensure the event loop is properly managed
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Use `create_task` if already in an event loop (like Celery)
            task = loop.create_task(
                fetch_matches_and_cache(
                    fetch_func=fetch_football_matches_async,
                    cache_key=f"matches_{league}",
                    fetch_args=(league_url,),
                    logger=logger,
                    process_func=process_football_matches,
                )
            )
            loop.run_until_complete(task)
        else:
            asyncio.run(
                fetch_matches_and_cache(
                    fetch_func=fetch_football_matches_async,
                    cache_key=f"matches_{league}",
                    fetch_args=(league_url,),
                    logger=logger,
                    process_func=process_football_matches,
                )
            )
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
