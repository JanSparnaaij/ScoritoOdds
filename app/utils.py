import asyncio
from flask import current_app
from playwright.async_api import async_playwright
from app.fetchers import fetch_tennis_matches_async

import asyncio
import json
from flask import current_app


async def fetch_matches_and_cache(fetch_func, cache_key, fetch_args, logger, process_func):
    """
    Asynchronously fetch data using the fetch_func, process it using process_func, and cache the result.

    Args:
        fetch_func (callable): Async function to fetch data (e.g., fetch_tennis_matches_async).
        cache_key (str): Redis key to store the cached data.
        fetch_args (tuple): Arguments to pass to the fetch_func.
        logger (Logger): Logger instance for logging messages.
        process_func (callable): Function to process fetched data before caching.

    Returns:
        None
    """
    try:
        logger.info(f"Starting data fetch for cache_key: {cache_key}")

        # Fetch data asynchronously
        data = await fetch_func(*fetch_args)

        if not data:
            logger.warning(f"No data fetched for cache_key: {cache_key}")
            return

        # Process the data
        processed_data = await asyncio.to_thread(process_func, data)  # Run sync function in thread pool
        if not processed_data:
            logger.warning(f"Processing returned no data for cache_key: {cache_key}")
            return

        # Cache the processed data
        redis_client = current_app.redis_client
        await asyncio.to_thread(redis_client.set, cache_key, json.dumps(processed_data))
        logger.info(f"Successfully cached data under key: {cache_key}")

    except Exception as e:
        logger.error(f"Error in fetch_matches_and_cache for cache_key {cache_key}: {e}")

async def fetch_combined_tennis_data(matches_url: str, rounds_url: str) -> list:
    """
    Asynchronously fetch combined tennis match data from the given URLs.

    Args:
        matches_url (str): The URL of the matches page.
        rounds_url (str): The URL of the rounds page (not currently used).

    Returns:
        list: A list of dictionaries containing match details and odds.
    """
    try:
        return await fetch_tennis_matches_async(matches_url)
    except Exception as e:
        print(f"Error fetching combined tennis data: {e}")
        return []

def log_task_status(logger, status, task_name, league=None):
    """
    Log the status of a Celery task in a structured format.
    
    Args:
        logger: The logger instance to log messages.
        status (str): The current status of the task (e.g., "start", "complete").
        task_name (str): The name of the Celery task.
        league (str, optional): The league name related to the task.
    """
    log_message = f"Task {task_name} has {status}."
    if league:
        log_message += f" League: {league}"
    logger.info(log_message)
