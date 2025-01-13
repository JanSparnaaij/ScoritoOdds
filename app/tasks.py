from app.celery_worker import create_celery_app
from app.football_fetcher import fetch_all_matches_async
from app.tennis_fetcher import fetch_combined_tennis_data
from app import cache
import asyncio

celery = create_celery_app()

@celery.task
def fetch_matches_in_background(league):
    """Fetch football matches in the background."""
    from app.routes import LEAGUES
    url = LEAGUES.get(league, LEAGUES['eredivisie'])
    matches = asyncio.run(fetch_all_matches_async(url))
    cache.set(f"matches_{league}", matches, timeout=3600)  # Cache in Redis
    return matches

@celery.task
def fetch_tennis_matches_in_background(league):
    """Fetch tennis matches in the background."""
    from app.routes import TENNIS_LEAGUES
    league_urls = TENNIS_LEAGUES.get(league, TENNIS_LEAGUES['atp_australian_open'])
    matches = asyncio.run(fetch_combined_tennis_data(league_urls['matches'], league_urls['rounds']))
    cache.set(f"tennis_matches_{league}", matches, timeout=3600)  # Cache in Redis
    return matches
