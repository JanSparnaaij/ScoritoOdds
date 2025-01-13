from app.celery_worker import celery
from app.tennis_fetcher import fetch_combined_tennis_data
from app.football_fetcher import fetch_all_matches_async
from app import cache
from blinker import signal

# Signals
fetch_tennis_signal = signal('fetch-tennis')
fetch_football_signal = signal('fetch-football')

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
    """
    Fetch tennis matches in the background and cache them.

    Args:
        league (str): The tennis league identifier.
    """
    from app.routes import TENNIS_LEAGUES  # Local import to avoid circular dependencies
    league_urls = TENNIS_LEAGUES.get(league, TENNIS_LEAGUES['atp_australian_open'])
    matches = fetch_combined_tennis_data(league_urls['matches'], league_urls['rounds'])
    cache.set(f"tennis_matches_{league}", matches, timeout=3600)

@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    """
    Fetch football matches in the background and cache them.

    Args:
        league (str): The football league identifier.
    """
    from app.routes import LEAGUES  # Local import to avoid circular dependencies
    url = LEAGUES.get(league, LEAGUES['eredivisie'])
    matches = fetch_all_matches_async(url)
    cache.set(f"matches_{league}", matches, timeout=3600)

# Connect tasks to signals
@fetch_tennis_signal.connect
def handle_fetch_tennis_signal(sender, league):
    """
    Handle the signal to fetch tennis matches.

    Args:
        sender: The sender of the signal.
        league (str): The tennis league identifier.
    """
    fetch_tennis_matches_in_background.delay(league)

@fetch_football_signal.connect
def handle_fetch_football_signal(sender, league):
    """
    Handle the signal to fetch football matches.

    Args:
        sender: The sender of the signal.
        league (str): The football league identifier.
    """
    fetch_matches_in_background.delay(league)
