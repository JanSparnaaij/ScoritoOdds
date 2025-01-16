from app.celery_worker import celery
from app.tennis_fetcher import fetch_combined_tennis_data
from app.football_fetcher import fetch_all_matches_async
from app.player_ratings import PLAYER_RATINGS
from flask import Flask
import asyncio
import logging
import json
import sys
import os

logger = logging.getLogger(__name__)

def get_app_context():
    """Create and return a Flask app instance."""
    # Ensure the base directory is in the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(project_root, ".."))

    from app import create_app
    return create_app()

@celery.task(name="app.tasks.fetch_tennis_matches_in_background")
def fetch_tennis_matches_in_background(league):
    """Fetch and process tennis matches for a specific league."""
    app = get_app_context()
    with app.app_context():
        app.logger.info(f"Task started for league: {league}")
        from app.constants import TENNIS_LEAGUES
        league_urls = TENNIS_LEAGUES.get(league, {})
        matches_url = league_urls.get("matches")
        rounds_url = league_urls.get("rounds")

        if not matches_url:
            app.logger.warning(f"Invalid league: {league}")
            return

        try:
            # Fetch matches
            matches = fetch_combined_tennis_data(matches_url, rounds_url)
            app.logger.info(f"Tennis matches retrieved: {len(matches)} matches fetched for {league}.")

            # Process matches
            processed_matches = []
            for match in matches:
                try:
                    # Extract match details
                    player1 = match.get("home_player", "Unknown")
                    player2 = match.get("away_player", "Unknown")
                    odds_player1 = match.get("odds", {}).get("home", None)
                    odds_player2 = match.get("odds", {}).get("away", None)

                    # Assign player categories and points
                    category1 = PLAYER_RATINGS.get(player1, "E")
                    category2 = PLAYER_RATINGS.get(player2, "E")
                    points1 = {"A": 20, "B": 40, "C": 60, "D": 90}.get(category1, 0)
                    points2 = {"A": 20, "B": 40, "C": 60, "D": 90}.get(category2, 0)

                    # Calculate expected points
                    prob1 = 1 / float(odds_player1) if odds_player1 else 0
                    prob2 = 1 / float(odds_player2) if odds_player2 else 0
                    expected_points1 = round(prob1 * points1, 2)
                    expected_points2 = round(prob2 * points2, 2)

                    # Add processed match to the list
                    processed_matches.append({
                        "date": match.get("date", "Unknown"),
                        "round": match.get("round", "Unknown"),
                        "players": {
                            "player1": player1,
                            "player2": player2,
                        },
                        "categories": {
                            "player1": category1,
                            "player2": category2,
                        },
                        "odds": {
                            "player1": odds_player1,
                            "player2": odds_player2,
                        },
                        "expected_points": {
                            "player1": expected_points1,
                            "player2": expected_points2,
                        },
                    })
                except Exception as e:
                    app.logger.warning(f"Error processing match: {match}. Error: {e}")
                    continue

            # Log processed matches
            app.logger.info(f"Processed {len(processed_matches)} matches for league {league}.")

            # Store in Redis
            cache_key = f"tennis_matches_{league}"
            app.redis_client.set(cache_key, json.dumps(processed_matches), ex=3600)
            app.logger.info(f"Tennis data for {league} successfully cached.")
        except Exception as e:
            app.logger.error(f"Error fetching tennis data for {league}: {e}")

@celery.task(name="app.tasks.fetch_matches_in_background")
def fetch_matches_in_background(league):
    """Fetch and store football matches for a specific league."""
    app = get_app_context()
    with app.app_context():
        from app.constants import LEAGUES

        # Validate league
        url = LEAGUES.get(league)
        if not url:
            app.logger.warning(f"Invalid league: {league}")
            return

        # Check if this task is already completed or running
        cache_key = f"matches_{league}"
        task_lock_key = f"fetch_task_{league}"
        if app.redis_client.exists(task_lock_key):
            app.logger.info(f"Task for league {league} is already running. Skipping.")
            return
        app.redis_client.set(task_lock_key, "running", ex=300)  # Lock task for 5 minutes

        try:
            # Check for existing cached data
            if app.redis_client.exists(cache_key):
                app.logger.info(f"Cached data for league {league} already exists. Skipping fetch.")
                return

            # Fetch matches asynchronously
            loop = asyncio.get_event_loop()
            matches = loop.run_until_complete(fetch_all_matches_async(url))

            if not matches:
                app.logger.warning(f"No matches found for league {league}.")
                return

            # Log retrieved matches
            app.logger.info(f"Matches retrieved: {len(matches)} matches fetched for {league}.")

            # Process matches
            processed_matches = []
            for match in matches:
                try:
                    processed_matches.append({
                        "home_team": match.get("home_team", "").strip(),
                        "away_team": match.get("away_team", "").strip(),
                        "odds": {
                            "home": match.get("odds", {}).get("home", "").strip(),
                            "draw": match.get("odds", {}).get("draw", "").strip(),
                            "away": match.get("odds", {}).get("away", "").strip(),
                        },
                    })
                except Exception as e:
                    app.logger.warning(f"Error processing match: {match}. Error: {e}")
                    continue

            # Cache processed matches
            if processed_matches:
                app.redis_client.set(cache_key, json.dumps(processed_matches), ex=3600)  # Cache for 1 hour
                app.logger.info(f"Football data for {league} successfully cached.")
            else:
                app.logger.warning(f"No valid matches processed for league: {league}")

        except Exception as e:
            app.logger.error(f"Error fetching football data for {league}: {e}")
        finally:
            # Release task lock
            app.redis_client.delete(task_lock_key)

@celery.task(name="app.tasks.test_task")
def test_task():
    print("Test task executed.")
    return "Success"
