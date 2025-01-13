import logging
import requests
from bs4 import BeautifulSoup
from app.player_ratings import PLAYER_RATINGS

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("TennisFetcher")

def fetch_combined_tennis_data(matches_url, rounds_url):
    """
    Fetch combined tennis data from matches and rounds URLs.

    Args:
        matches_url (str): URL for the match data.
        rounds_url (str): URL for the round data.

    Returns:
        list: A list of dictionaries containing match data.
    """
    match_data = []

    try:
        # Fetch round data
        logger.warning(f"Fetching content from: {rounds_url}")
        rounds_response = requests.get(rounds_url)
        rounds_soup = BeautifulSoup(rounds_response.content, "html.parser")

        # Extract round names (update CSS selectors as necessary)
        rounds = rounds_soup.select(".round-name-selector")  # Placeholder selector
        round_names = [round_.text.strip() for round_ in rounds if round_.text]
        logger.info(f"Extracted rounds: {round_names}")
    except Exception as e:
        logger.error(f"Failed to fetch or parse round data: {e}")
        round_names = []

    try:
        # Fetch match data
        logger.warning(f"Fetching content from: {matches_url}")
        matches_response = requests.get(matches_url)
        matches_soup = BeautifulSoup(matches_response.content, "html.parser")

        # Extract match containers (update CSS selectors as necessary)
        match_containers = matches_soup.select(".match-container-selector")  # Placeholder selector

        for match in match_containers:
            try:
                player1 = match.select_one(".player1-name-selector").text.strip()
                player2 = match.select_one(".player2-name-selector").text.strip()

                odds_player1 = match.select_one(".player1-odds-selector").text.strip()
                odds_player2 = match.select_one(".player2-odds-selector").text.strip()

                odds_player1 = float(odds_player1) if odds_player1 else None
                odds_player2 = float(odds_player2) if odds_player2 else None

                probabilities = {
                    "player1": round(100 / odds_player1, 2) if odds_player1 else None,
                    "player2": round(100 / odds_player2, 2) if odds_player2 else None,
                }

                match_info = {
                    "players": {
                        "player1": player1,
                        "player2": player2,
                    },
                    "odds": {
                        "player1": odds_player1,
                        "player2": odds_player2,
                    },
                    "probabilities": probabilities,
                    "ratings": {
                        "player1": PLAYER_RATINGS.get(player1, "Unknown"),
                        "player2": PLAYER_RATINGS.get(player2, "Unknown"),
                    },
                    "round": "Unknown",  # Default round value, updated below
                    "date": "Unknown",  # Placeholder for date if available
                }

                # Assign round names if available
                if round_names:
                    match_info["round"] = round_names.pop(0) if round_names else "Unknown"

                match_data.append(match_info)

            except Exception as match_error:
                logger.warning(f"Error parsing match: {match_error}")
    except Exception as e:
        logger.error(f"Failed to fetch or parse match data: {e}")

    return match_data
