import asyncio
from flask import current_app
from playwright.async_api import async_playwright
from app.fetchers import fetch_tennis_matches_async

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
        # Log the start of the fetch operation
        print(f"Fetching tennis data from: {matches_url}")
        
        # Fetch asynchronously using `fetch_tennis_matches_async`
        data = await fetch_tennis_matches_async(matches_url)
        
        # Log the results
        if not data:
            print(f"No data found for URL: {matches_url}")
        else:
            print(f"Successfully fetched {len(data)} matches from {matches_url}")
        
        return data
    except Exception as e:
        # Handle and log errors gracefully
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
