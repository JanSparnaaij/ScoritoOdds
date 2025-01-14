from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.player_ratings import PLAYER_RATINGS
from app import cache, db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from blinker import signal
import re

# Blueprints
main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)

# Signal definitions
fetch_tennis_signal = signal("fetch-tennis")
fetch_football_signal = signal("fetch-football")

# League URLs
LEAGUES = {
    "eredivisie": "https://www.oddsportal.com/football/netherlands/eredivisie/",
    "eerste_divisie": "https://www.oddsportal.com/football/netherlands/eerste-divisie/",
    "premier_league": "https://www.oddsportal.com/football/england/premier-league/",
}

TENNIS_LEAGUES = {
    "atp_australian_open": {
        "matches": "https://www.oddsportal.com/tennis/australia/atp-australian-open/",
        "rounds": "https://www.oddsportal.com/tennis/australia/atp-australian-open/standings/",
    },
}

# Signal Handlers
@fetch_football_signal.connect
def handle_fetch_football(sender, league):
    from app.tasks import fetch_matches_in_background
    current_app.logger.info(f"Signal received to fetch football data for league: {league}")
    fetch_matches_in_background.delay(league)

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
    matches = cache.get(cache_key)

    if not matches:
        flash("Data is being fetched; check back shortly.", "info")
        fetch_football_signal.send(current_app._get_current_object(), league=selected_league)

    return render_template("football.html", matches=matches or [], leagues=LEAGUES, selected_league=selected_league)

@main_bp.route("/tennis")
async def tennis():
    if "user_id" not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("auth.login"))

    selected_league = request.args.get("league", "atp_australian_open")
    cache_key = f"tennis_matches_{selected_league}"
    matches = cache.get(cache_key)

    if not matches:
        flash("Data is being fetched; check back shortly.", "info")
        fetch_tennis_signal.send(current_app._get_current_object(), league=selected_league)

    return render_template("tennis.html", matches=matches or [], leagues=TENNIS_LEAGUES, selected_league=selected_league)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

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

        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose another one.", "danger")
        else:
            hashed_password = generate_password_hash(password, method="sha256")
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
