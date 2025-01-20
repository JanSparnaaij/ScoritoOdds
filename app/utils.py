import asyncio
from flask import current_app
from playwright.async_api import async_playwright
from app.fetchers import fetch_tennis_matches_async

import asyncio
import json
from flask import current_app


async def fetch_matches_and_cache(fetch_func, cache_key, fetch_args, logger):
    """
    Asynchronously fetch data using the fetch_func, process it using process_func, and cache the result.

    Args:
        fetch_func (callable): Async function to fetch data (e.g., fetch_tennis_matches_async).
        cache_key (str): Redis key to store the cached data.
        fetch_args (tuple): Arguments to pass to the fetch_func.
        logger (Logger): Logger instance for logging messages.

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
        
        logger.debug(f"Fetched data: {data}")

        # Cache the fetched data
        redis_client = current_app.redis_client
        await asyncio.to_thread(redis_client.set, cache_key, json.dumps(data))
        logger.info(f"Successfully cached data under key: {cache_key}")

    except Exception as e:
        logger.error(f"Error in fetch_matches_and_cache for cache_key {cache_key}: {e}")

async def fetch_combined_tennis_data(matches_url: str, rounds_url: str) -> list:
    try:
        data = await fetch_tennis_matches_async(matches_url)
        if not data:
            print(f"No data fetched from: {matches_url}")
        else:
            print(f"Fetched {len(data)} matches from: {matches_url}")
        return data
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
