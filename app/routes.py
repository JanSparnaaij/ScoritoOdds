from flask import Flask, render_template, request
from flask_caching import Cache
from app.football_fetcher import fetch_all_matches
from app.tennis_fetcher import fetch_tennis_matches

app = Flask(__name__)

# Configure caching
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 3600  # Cache timeout in seconds (1 hour)
cache = Cache(app)

# Define the leagues and their URLs
LEAGUES = {
    "eredivisie": "https://www.oddsportal.com/soccer/netherlands/eredivisie/",
    "premier_league": "https://www.oddsportal.com/football/england/premier-league/",
}

TENNIS_LEAGUES = {
    "atp_australian_open": "https://www.oddsportal.com/tennis/australia/atp-australian-open/",
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
    """Tennis page with league selection."""
    selected_league = request.args.get('league', 'atp_australian_open')
    url = TENNIS_LEAGUES.get(selected_league, TENNIS_LEAGUES['atp_australian_open'])
    matches = fetch_tennis_matches(url)
    return render_template('tennis.html', matches=matches, leagues=TENNIS_LEAGUES, selected_league=selected_league)
