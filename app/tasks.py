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
    """Fetch and store tennis matches for a specific league."""
    app = get_app_context()
    with app.app_context():
        from app.constants import TENNIS_LEAGUES
        league_urls = TENNIS_LEAGUES.get(league, {})
        matches_url = league_urls.get("matches")
        rounds_url = league_urls.get("rounds")

        if not matches_url:
            logger.warning(f"Invalid league: {league}")
            return

        try:
            matches = fetch_combined_tennis_data(matches_url, rounds_url)

            # Log matches to verify structure
            app.logger.info(f"Tennis matches retrieved: {len(matches)} matches fetched for {league}.")

            # Process matches
            processed_matches = []
            for match in matches:
                try:
                    # Fetch player names and odds
                    player1, player2 = match["players"]
                    odds_player1, odds_player2 = match["odds"]

                    # Fetch player categories and points
                    category1 = PLAYER_RATINGS.get(player1, "D")
                    category2 = PLAYER_RATINGS.get(player2, "D")

                    points1 = {"A": 20, "B": 40, "C": 60, "D": 90}[category1]
                    points2 = {"A": 20, "B": 40, "C": 60, "D": 90}[category2]

                    # Calculate expected points
                    prob1 = 1 / float(odds_player1) if odds_player1 else 0
                    prob2 = 1 / float(odds_player2) if odds_player2 else 0

                    expected_points1 = round(prob1 * points1, 2)
                    expected_points2 = round(prob2 * points2, 2)

                    # Add processed match to the list
                    processed_matches.append({
                        "date": match.get("date", ""),
                        "round": match.get("round", ""),
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
        url = LEAGUES.get(league, LEAGUES["eredivisie"])
        app.logger.info(f"Fetching football matches for league: {league} with URL: {url}")

        try:
            # Fetch matches
            loop = asyncio.get_event_loop()
            matches = loop.run_until_complete(fetch_all_matches_async(url))

            # Log matches to verify structure
            app.logger.info(f"Matches retrieved: {len(matches)} matches fetched for {league}.")

            # Add timeout handling for each match processing
            processed_matches = []
            for idx, match in enumerate(matches):
                try:
                    # Process each match individually
                    processed_matches.append({
                        "home_team": match.get("home_team", ""),
                        "away_team": match.get("away_team", ""),
                        "odds": {
                            "home": match["odds"].get("home", ""),
                            "draw": match["odds"].get("draw", ""),
                            "away": match["odds"].get("away", "")
                        }
                    })
                except KeyError as e:
                    app.logger.warning(f"KeyError processing match {idx}: {e}")
                except Exception as e:
                    app.logger.warning(f"Error processing match {idx}: {e}")
                    continue  # Skip to the next match

            # Log processed matches
            app.logger.info(f"Processed matches: {processed_matches}")

            # Store in Redis
            if processed_matches:
                app.redis_client.set(f"matches_{league}", json.dumps(processed_matches), ex=3600)
                app.logger.info(f"Football data for {league} successfully cached.")
            else:
                app.logger.warning(f"No valid matches processed for league: {league}")
        except Exception as e:
            logger.error(f"Error fetching football data for {league}: {e}")