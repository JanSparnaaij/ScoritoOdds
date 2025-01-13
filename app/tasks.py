from app.celery_worker import celery
from app.football_fetcher import fetch_all_matches_async
from app.tennis_fetcher import fetch_combined_tennis_data
from app import cache
import asyncio

@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    """
    Fetch football matches in the background and cache the result.
    Args:
        league (str): The league identifier
    """
    from app.routes import LEAGUES  
    url = LEAGUES.get(league, LEAGUES['eredivisie'])  # Default to 'eredivisie' if league is not found
    matches = asyncio.run(fetch_all_matches_async(url))
    cache.set(f"matches_{league}", matches, timeout=3600)  # Cache matches in Redis
    return matches

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
    """
    Fetch tennis matches in the background and cache the result.
    Args:
        league (str): The tennis league identifier
    """
    from app.routes import TENNIS_LEAGUES  
    league_urls = TENNIS_LEAGUES.get(league, TENNIS_LEAGUES['atp_australian_open'])  # Default league
    matches = asyncio.run(fetch_combined_tennis_data(league_urls['matches'], league_urls['rounds']))
    cache.set(f"tennis_matches_{league}", matches, timeout=3600)  # Cache matches in Redis
    return matches
