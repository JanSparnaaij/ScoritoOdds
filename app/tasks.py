# Signals
fetch_tennis_signal = signal('fetch-tennis')
fetch_football_signal = signal('fetch-football')

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
    """Fetch tennis matches in the background and cache them."""
    from app.routes import TENNIS_LEAGUES
    league_urls = TENNIS_LEAGUES.get(league, TENNIS_LEAGUES['atp_australian_open'])
    matches = fetch_combined_tennis_data(league_urls['matches'], league_urls['rounds'])
    cache.set(f"tennis_matches_{league}", matches, timeout=3600)

@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    """Fetch football matches in the background and cache them."""
    from app.routes import LEAGUES
    url = LEAGUES.get(league, LEAGUES['eredivisie'])
    matches = fetch_all_matches_async(url)
    cache.set(f"matches_{league}", matches, timeout=3600)

# Connect tasks to signals
@fetch_tennis_signal.connect
def handle_fetch_tennis_signal(sender, league):
    fetch_tennis_matches_in_background.delay(league)

@fetch_football_signal.connect
def handle_fetch_football_signal(sender, league):
    fetch_matches_in_background.delay(league)
