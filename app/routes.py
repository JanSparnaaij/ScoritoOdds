from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from blinker import signal
from app.constants import LEAGUES, TENNIS_LEAGUES
import re
import json
from app.models import db, User  # Lazy import of db

# Blueprints
main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)

# Signal definitions
fetch_tennis_signal = signal("fetch-tennis")
fetch_football_signal = signal("fetch-football")

# Signal Handlers
@fetch_football_signal.connect
def handle_fetch_football(sender, league):
    from app.tasks import fetch_football_in_background
    current_app.logger.info(f"Signal received to fetch football data for league: {league}")
    fetch_football_in_background.delay(league)

@fetch_tennis_signal.connect
def handle_fetch_tennis(sender, league):
    from app.tasks import fetch_tennis_matches_in_background
    current_app.logger.info(f"Signal received to fetch tennis data for league: {league}")
    fetch_tennis_matches_in_background.delay(league)

# Routes
@main_bp.route("/")
def home():
    return render_template("home.html")

@main_bp.route("/football")
async def football():
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("auth.login"))

    selected_league = request.args.get("league", "eredivisie")
    cache_key = f"matches_{selected_league}"
    matches = current_app.redis_client.get(cache_key)
    
    if matches:
        matches = json.loads(matches.decode("utf-8")) 
        loading = False
        current_app.logger.info(f"Cache hit for league '{selected_league}': {len(matches)} matches retrieved.")
    else:
        flash("Data is being fetched; check back shortly.", "info")
        fetch_football_signal.send(current_app._get_current_object(), league=selected_league)
        current_app.logger.info(f"Cache miss for league '{selected_league}'. Signal sent to fetch matches.")
        loading = True

    return render_template("football.html", matches=matches or [], leagues=LEAGUES, selected_league=selected_league, loading=loading)

@main_bp.route("/tennis")
async def tennis():
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("auth.login"))

    selected_league = request.args.get("league", "atp_australian_open")
    cache_key = f"tennis_matches_{selected_league}"
    matches = current_app.redis_client.get(cache_key)

    if matches:
        matches = json.loads(matches.decode("utf-8"))
        # Sort matches by highest expected points
        matches.sort(
            key=lambda match: max(
                match["expected_points"].get("home", 0),
                match["expected_points"].get("away", 0),
            ),
            reverse=True,
        )
        loading = False
        current_app.logger.info(f"Cache hit for league '{selected_league}': {len(matches)} matches retrieved.")
    else:
        flash("Data is being fetched; check back shortly.", "info")
        fetch_tennis_signal.send(current_app._get_current_object(), league=selected_league)
        current_app.logger.info(f"Cache miss for league '{selected_league}'. Signal sent to fetch matches.")
        loading = True
        matches = []

    return render_template("tennis.html", matches=matches, leagues=TENNIS_LEAGUES, selected_league=selected_league, loading=loading)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    from flask import current_app
    current_app.logger.info(f"App context: {current_app}")
    current_app.logger.info(f"DB instance type: {type(db)}")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
       
        try:
            user = User.query.filter_by(username=username).first()
        except Exception as e:
            current_app.logger.error(f"Error querying the database: {e}")
            flash("An error occurred while processing your request.", "danger")
            return render_template("login.html")

        if user and check_password_hash(user.password, password):
            session.clear()
            session["user_id"] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.home"))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[A-Z]", password):
            flash("Password must be at least 8 characters long, contain a number, and an uppercase letter.", "danger")
            return redirect(url_for("auth.signup"))

        if db.session.query(User).filter_by(username=username).first():
            flash("Username already exists. Please choose another one.", "danger")
        else:
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("signup.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.home"))

@main_bp.route("/redis")
def test_redis():
    try:
        current_app.redis_client.set("test_key", "test_value", ex=60)
        value = current_app.redis_client.get("test_key")
        return f"Redis connected. Retrieved value: {value}"
    except Exception as e:
        return f"Redis connection failed: {e}", 500

@main_bp.route("/cache")
def test_cache():
    try:
        current_app.redis_client.set("test_key", "test_value", ex=60)
        value = current_app.redis_client.get("test_key")
        return f"Cache connected. Retrieved value: {value}"
    except Exception as e:
        return f"Cache connection failed: {e}", 500
    
@main_bp.route("/test-redis-matches")
def test_redis_matches():
    try:
        value = current_app.redis_client.get(f"matches_eredivisie")
        if value:
            # Decode and print the value (assuming JSON serialization)
            value = value.decode("utf-8")
            return f"Matches retrieved: {value}"
        else:
            return "No matches found in Redis for 'matches_eredivisie'."
    except Exception as e:
        return f"Error retrieving matches: {e}", 500

@main_bp.route("/test-redis-write")
def test_redis_write():
    try:
        test_data = [{"match_id": "test123", "home": "Team A", "away": "Team B", "odds": {"home": 1.5, "draw": 3.2, "away": 5.0}}]
        current_app.redis_client.set("matches_eredivisie", json.dumps(test_data), ex=3600)
        return "Test data written to Redis."
    except Exception as e:
        return f"Error writing to Redis: {e}", 500

@main_bp.route("/test-redis-read")
def test_redis_read():
    try:
        value = current_app.redis_client.get("matches_eredivisie")
        if value:
            matches = json.loads(value.decode("utf-8"))
            return f"Test data retrieved: {matches}"
        return "No data found for 'matches_eredivisie'."
    except Exception as e:
        return f"Error reading from Redis: {e}", 500
    
@main_bp.route("/clear-data")
def clear_test_data():
    try:
        keys_to_clear = ["matches_eredivisie"]
        for key in keys_to_clear:
            current_app.redis_client.delete(key)
        return "Test data cleared."
    except Exception as e:
        return f"Error clearing test data: {e}", 500

@main_bp.route("/clear-tennis-cache")
def clear_tennis_cache():
    """Clear tennis cache for debugging."""
    key = f"tennis_matches_atp_australian_open"
    current_app.redis_client.delete(key)
    return "Tennis cache cleared."

@main_bp.route("/debug-tennis-data")
def debug_tennis_data():
    key = f"tennis_matches_atp_australian_open"  # Use the league you are testing
    value = current_app.redis_client.get(key)
    if value:
        matches = json.loads(value.decode("utf-8"))
        return matches  # This will return the data directly as JSON
    return "No data found for the specified key."

@main_bp.route("/celery")
def test_celery():
    from app.tasks import fetch_tennis_matches_in_background
    task = fetch_tennis_matches_in_background.delay("atp_australian_open")
    return f"Task {task.id} sent to Celery"
