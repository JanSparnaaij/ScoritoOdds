from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.football_fetcher import fetch_all_matches
from app.tennis_fetcher import fetch_tennis_matches
from app.player_ratings import PLAYER_RATINGS
from app import cache, db
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User

# Blueprint for main routes
main_bp = Blueprint('main', __name__)

LEAGUES = {
    "eredivisie": "https://www.oddsportal.com/soccer/netherlands/eredivisie/",
    "premier_league": "https://www.oddsportal.com/football/england/premier-league/",
    "jupiler_pro_league": "https://www.oddsportal.com/football/belgium/jupiler-pro-league/",
}

TENNIS_LEAGUES = {
    "atp_australian_open": "https://www.oddsportal.com/tennis/australia/atp-australian-open/",
    "wta_australian_open": "https://www.oddsportal.com/tennis/australia/wta-australian-open/",
}

@main_bp.route('/')
def home():
    """Homepage"""
    return render_template('home.html')

@main_bp.route('/football')
def football():
    """Football page"""
    print(f"SECRET_KEY during request: {current_app.config.get('SECRET_KEY')}")
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    selected_league = request.args.get('league', 'eredivisie')
    cache_key = f"matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        url = LEAGUES.get(selected_league, LEAGUES['eredivisie'])
        matches = fetch_all_matches(url)
        cache.set(cache_key, matches)

    return render_template('football.html', matches=matches, leagues=LEAGUES, selected_league=selected_league)

@main_bp.route('/tennis')
def tennis():
    """Tennis page"""
    print(f"SECRET_KEY during request: {current_app.config.get('SECRET_KEY')}")
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))

    selected_league = request.args.get('league', 'atp_australian_open')
    selected_category = request.args.get('category', 'all')
    url = TENNIS_LEAGUES.get(selected_league, TENNIS_LEAGUES['atp_australian_open'])

    cache_key = f"tennis_matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        matches = fetch_tennis_matches(url, PLAYER_RATINGS)
        cache.set(cache_key, matches)

    if selected_category != 'all':
        matches = [
            match for match in matches
            if match["players"]["player1_rating"] == selected_category or
               match["players"]["player2_rating"] == selected_category
        ]

    matches.sort(key=lambda x: max(x["expected_points"]["player1"], x["expected_points"]["player2"]), reverse=True)

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
