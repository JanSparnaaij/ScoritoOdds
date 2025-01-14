from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.player_ratings import PLAYER_RATINGS
from app import cache, db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from blinker import signal
import re
import requests
from bs4 import BeautifulSoup

# Blueprint for main routes
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)

# Signal definitions
fetch_tennis_signal = signal('fetch-tennis')
fetch_football_signal = signal('fetch-football')

# League URLs
LEAGUES = {
    "eredivisie": "https://www.oddsportal.com/football/netherlands/eredivisie/",
    "eerste_divisie": "https://www.oddsportal.com/football/netherlands/eerste-divisie/",
    "premier_league": "https://www.oddsportal.com/football/england/premier-league/",
}

TENNIS_LEAGUES = {
    "atp_australian_open": {
        "matches": "https://www.oddsportal.com/tennis/australia/atp-australian-open/",
    },
}

# Scraping Functions
def scrape_football(league_url):
    """Scrape football matches from the given league URL."""
    try:
        response = requests.get(league_url)
        soup = BeautifulSoup(response.text, "html.parser")

        matches = []
        for match in soup.select(".match-row"):  # Update this selector to match the website's structure
            home = match.select_one(".home-team").text.strip()
            away = match.select_one(".away-team").text.strip()
            date = match.select_one(".match-date").text.strip()
            odds = {
                "home": float(match.select_one(".home-odds").text.strip()),
                "draw": float(match.select_one(".draw-odds").text.strip()),
                "away": float(match.select_one(".away-odds").text.strip()),
            }
            matches.append({"home": home, "away": away, "date": date, "odds": odds})

        return matches
    except Exception as e:
        current_app.logger.error(f"Error scraping football data: {e}")
        return []

def scrape_tennis(league_url):
    """Scrape tennis matches from the given league URL."""
    try:
        response = requests.get(league_url)
        soup = BeautifulSoup(response.text, "html.parser")

        matches = []
        for match in soup.select(".match-row"):  # Update this selector to match the website's structure
            players = {
                "player1": match.select_one(".player1").text.strip(),
                "player2": match.select_one(".player2").text.strip(),
            }
            date = match.select_one(".match-date").text.strip()
            matches.append({"players": players, "date": date})

        return matches
    except Exception as e:
        current_app.logger.error(f"Error scraping tennis data: {e}")
        return []

# Signal Handlers
@fetch_football_signal.connect
def handle_fetch_football(sender, league):
    league_url = LEAGUES.get(league)
    if league_url:
        matches = scrape_football(league_url)
        cache.set(f"matches_{league}", matches, timeout=3600)

@fetch_tennis_signal.connect
def handle_fetch_tennis(sender, league):
    league_url = TENNIS_LEAGUES.get(league, {}).get("matches")
    if league_url:
        matches = scrape_tennis(league_url)
        cache.set(f"tennis_matches_{league}", matches, timeout=3600)

# Homepage
@main_bp.route('/')
def home():
    """Homepage"""
    return render_template('home.html')

# Football Page
@main_bp.route('/football')
async def football():
    """Football page"""
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    selected_league = request.args.get('league', 'eredivisie')
    cache_key = f"matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        flash("Data is being fetched; check back shortly.", "info")
        fetch_football_signal.send(current_app._get_current_object(), league=selected_league)

    return render_template('football.html', matches=matches or [], leagues=LEAGUES, selected_league=selected_league)

# Tennis Page
@main_bp.route('/tennis')
async def tennis():
    """Tennis page"""
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    selected_league = request.args.get('league', 'atp_australian_open')
    cache_key = f"tennis_matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        flash("Data is being fetched; check back shortly.", "info")
        fetch_tennis_signal.send(current_app._get_current_object(), league=selected_league)

    return render_template(
        'tennis.html',
        matches=matches or [],
        leagues=TENNIS_LEAGUES,
        selected_league=selected_league
    )

# The rest of the code remains unchanged
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[A-Z]", password):
            flash("Password must be at least 8 characters long, contain a number, and an uppercase letter.", 'danger')
            return redirect(url_for('auth.signup'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another one.', 'dan
