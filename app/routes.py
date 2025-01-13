from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.football_fetcher import fetch_all_matches_async
from app.tennis_fetcher import fetch_combined_tennis_data
from app.player_ratings import PLAYER_RATINGS
from app import cache, db
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app.tasks import fetch_matches_in_background, fetch_tennis_matches_in_background
import re

# Blueprint for main routes
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)

# League URLs
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
        fetch_matches_in_background.delay(selected_league)  # Queue task

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
        fetch_tennis_matches_in_background.delay(selected_league)  # Queue task

    return render_template('tennis.html', matches=matches or [], leagues=TENNIS_LEAGUES, selected_league=selected_league)

# Login Route
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
            current_app.logger.info(f"User {username} logged in.")
            return redirect(url_for('main.home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

# Signup Route
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[A-Z]", password):
            flash("Password must be at least 8 characters long, contain a number, and an uppercase letter.", "danger")
            return redirect(url_for('auth.signup'))

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

# Logout Route
@auth_bp.route('/logout')
def logout():
    """Logout page"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.home'))
