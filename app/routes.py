from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.football_fetcher import fetch_all_matches_async
from app.player_ratings import PLAYER_RATINGS
from app import cache, db
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.tennis_fetcher import fetch_combined_tennis_data

# Blueprint for main routes
main_bp = Blueprint('main', __name__)

LEAGUES = {
    "eredivisie": "https://www.oddsportal.com/football/netherlands/eredivisie/",
    "eerste_divisie": "https://www.oddsportal.com/football/netherlands/eerste-divisie/",
    "premier_league": "https://www.oddsportal.com/football/england/premier-league/",
    "jupiler_pro_league": "https://www.oddsportal.com/football/belgium/jupiler-pro-league/",
    "bundesliga": "https://www.oddsportal.com/football/germany/bundesliga/",
    "serie_a": "https://www.oddsportal.com/football/italy/serie-a/",
    "la_liga": "https://www.oddsportal.com/football/spain/laliga/",
    "champions_league": "https://www.oddsportal.com/football/europe/champions-league/",
    "europa_league": "https://www.oddsportal.com/football/europe/europa-league/",
}

TENNIS_LEAGUES = {
    "atp_australian_open": {
        "matches": "https://www.oddsportal.com/tennis/australia/atp-australian-open/",
        "rounds": "https://www.oddsportal.com/tennis/australia/atp-australian-open/standings/",
    }, 
    "wta_australian_open": {
        "matches": "https://www.oddsportal.com/tennis/australia/wta-australian-open/",
        "rounds": "https://www.oddsportal.com/tennis/australia/wta-australian-open/standings/",
    },   
}

@main_bp.route('/')
def home():
    """Homepage"""
    return render_template('home.html')

@main_bp.route('/football')
async def football():
    """Football page"""
    # User login check
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    selected_league = request.args.get('league', 'eredivisie')
    cache_key = f"matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        url = LEAGUES.get(selected_league, LEAGUES['eredivisie'])
        try:
            # Await the async function to fetch matches
            matches = await fetch_all_matches_async(url)
            cache.set(cache_key, matches)  # Cache the result
        except Exception as e:
            current_app.logger.error(f"Error fetching matches: {e}")
            flash("Unable to fetch matches at this time.", "danger")
            matches = []

    # Handle empty matches gracefully
    if not matches:
        flash("No matches could be fetched for the selected league.", "danger")

    return render_template('football.html', matches=matches, leagues=LEAGUES, selected_league=selected_league)

@main_bp.route('/tennis')
def tennis():
    """Tennis page"""
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    # Get selected league and category from query parameters
    selected_league = request.args.get('league', 'atp_australian_open')
    selected_category = request.args.get('category', 'all')
    league_urls = TENNIS_LEAGUES.get(selected_league, TENNIS_LEAGUES['atp_australian_open'])
    matches_url = league_urls['matches']
    rounds_url = league_urls['rounds']

    # Cache key to avoid redundant fetching
    cache_key = f"tennis_matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        # Fetch combined data (matches and rounds)
        matches = fetch_combined_tennis_data(matches_url, rounds_url, PLAYER_RATINGS)
        cache.set(cache_key, matches)

    # Filter matches by category if not 'all'
    if selected_category != 'all':
        matches = [
            match for match in matches
            if  match["players"].get("player1_rating") == selected_category or
                match["players"].get("player2_rating") == selected_category
        ]

    # Sort matches by highest expected points
    matches.sort(key=lambda x: max(x["expected_points"]["player1"], x["expected_points"]["player2"]), reverse=True)

    # Render the template
    return render_template(
        'tennis.html',
        matches=matches,
        leagues=TENNIS_LEAGUES,
        selected_league=selected_league,
        selected_category=selected_category,
        categories=["A", "B", "C", "D", "all"],
    )

# Routes for authentication
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another one.', 'danger')
        else:
            hashed_password = generate_password_hash(password, method='sha256')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    """Logout page."""
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.home'))
