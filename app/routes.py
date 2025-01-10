from flask import Flask, render_template, request
from flask_caching import Cache
from app.football_fetcher import fetch_all_matches
from app.tennis_fetcher import fetch_tennis_matches
from config import PLAYER_RATINGS

app = Flask(__name__)

# Configure caching
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 3600  # Cache timeout in seconds (1 hour)
cache = Cache(app)

# Define the leagues and their URLs
LEAGUES = {
    "eredivisie": "https://www.oddsportal.com/soccer/netherlands/eredivisie/",
    "premier_league": "https://www.oddsportal.com/football/england/premier-league/",
    "jupiler_pro_league": "https://www.oddsportal.com/football/belgium/jupiler-pro-league/",
}

TENNIS_LEAGUES = {
    "atp_australian_open": "https://www.oddsportal.com/tennis/australia/atp-australian-open/",
    "wta_australian_open": "https://www.oddsportal.com/tennis/australia/wta-australian-open/",
}

@app.route('/')
def home():
    """Homepage with sport selection."""
    return render_template('home.html')

@app.route('/football')
def football():
    """Football page with league selection."""
    selected_league = request.args.get('league', 'eredivisie')

    # Fetch matches from cache or refresh if expired
    cache_key = f"matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        print(f"Cache miss for league: {selected_league}. Fetching data...")
        url = LEAGUES.get(selected_league, LEAGUES['eredivisie'])
        matches = fetch_all_matches(url)
        cache.set(cache_key, matches)  # Cache the fetched matches
    else:
        print(f"Cache hit for league: {selected_league}")

    return render_template('football.html', matches=matches, leagues=LEAGUES, selected_league=selected_league)
@app.route('/tennis')
def tennis():
    """Tennis page with league selection, player ratings, and sorting."""
    selected_league = request.args.get('league', 'atp_australian_open')
    sort_by = request.args.get('sort_by', 'datetime')  # Default sorting is by datetime
    url = TENNIS_LEAGUES.get(selected_league, TENNIS_LEAGUES['atp_australian_open'])

    # Fetch matches with player ratings
    cache_key = f"tennis_matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        print(f"Cache miss for tennis league: {selected_league}. Fetching data...")
        matches = fetch_tennis_matches(url, PLAYER_RATINGS)
        cache.set(cache_key, matches)  # Cache the fetched matches
    else:
        print(f"Cache hit for tennis league: {selected_league}")

    # Sort matches based on the chosen parameter
    if sort_by == 'expected_points_player1':
        matches.sort(key=lambda x: x['expected_points']['player1'], reverse=True)
    elif sort_by == 'expected_points_player2':
        matches.sort(key=lambda x: x['expected_points']['player2'], reverse=True)

    return render_template(
        'tennis.html',
        matches=matches,
        leagues=TENNIS_LEAGUES,
        selected_league=selected_league,
        sort_by=sort_by
    )

