from playwright.async_api import async_playwright
from app import redis_client
import json
import logging
import asyncio

async def fetch_matches_and_cache(fetch_func, cache_key, fetch_args, logger, process_func):
    """
    Asynchronously fetch data using the fetch_func, process it using process_func, and cache the result.
    """
    try:
        logger.info(f"Starting data fetch for cache_key: {cache_key}")
        
        # Run the async fetch_func directly
        data = await fetch_func(*fetch_args)

        if not data:
            logger.warning(f"No data fetched for cache_key: {cache_key}")
            return

        # Process and cache the data
        processed_data = process_func(data)
        if not processed_data:
            logger.warning(f"Processing returned no data for cache_key: {cache_key}")
            return

        # Store in Redis (update if using aioredis)
        await asyncio.to_thread(redis_client.set, cache_key, json.dumps(processed_data))
        logger.info(f"Successfully cached data under key: {cache_key}")

    except Exception as e:
        logger.error(f"Error in fetch_matches_and_cache for cache_key {cache_key}: {str(e)}")

def log_task_status(logger, status, task_name, league=None):
    """
    Log the status of a Celery task in a structured format.
    """
    log_message = f"Task {task_name} has {status}."
    if league:
        log_message += f" League: {league}"
    logger.info(log_message)

async def get_browser(app):
    """Get or create a shared Playwright browser instance."""
    if not hasattr(app, "_playwright_browser"):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True, 
            args=["--disable-dev-shm-usage"]
        )
        app._playwright_browser = browser
        app._playwright_context = playwright
    return app._playwright_browser

async def close_browser(app):
    """Close the shared Playwright browser instance."""
    if hasattr(app, "_playwright_browser"):
        await app._playwright_browser.close()
        await app._playwright_context.stop()
        del app._playwright_browser
        del app._playwright_context
