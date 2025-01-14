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
    round_names = []

    try:
        # Fetch round data
        logger.info(f"Fetching round data from: {rounds_url}")
        rounds_response = requests.get(rounds_url, timeout=10)
        rounds_response.raise_for_status()

        rounds_soup = BeautifulSoup(rounds_response.content, "html.parser")
        rounds = rounds_soup.select(".round-name-selector")  # Update this selector
        round_names = [round_.text.strip() for round_ in rounds if round_.text]
        logger.debug(f"Extracted {len(round_names)} rounds: {round_names}")

    except Exception as e:
        logger.error(f"Failed to fetch or parse round data: {e}")

    try:
        # Fetch match data
        logger.info(f"Fetching match data from: {matches_url}")
        matches_response = requests.get(matches_url, timeout=10)
        matches_response.raise_for_status()

        matches_soup = BeautifulSoup(matches_response.content, "html.parser")
        match_containers = matches_soup.select(".match-container-selector")  # Update this selector
        logger.debug(f"Found {len(match_containers)} match containers.")

        for match in match_containers:
            try:
                # Extract player names
                player1_elem = match.select_one(".player1-name-selector")
                player2_elem = match.select_one(".player2-name-selector")
                if not player1_elem or not player2_elem:
                    logger.warning("Missing player names. Skipping match.")
                    continue

                player1 = player1_elem.text.strip()
                player2 = player2_elem.text.strip()

                # Extract odds
                odds_player1_elem = match.select_one(".player1-odds-selector")
                odds_player2_elem = match.select_one(".player2-odds-selector")
                odds_player1 = float(odds_player1_elem.text.strip()) if odds_player1_elem else None
                odds_player2 = float(odds_player2_elem.text.strip()) if odds_player2_elem else None

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
                    "round": "Unknown",  # Default round value
                    "date": "Unknown",  # Placeholder for date if available
                }

                # Assign round names cyclically if needed
                if round_names:
                    match_info["round"] = round_names.pop(0)
                else:
                    logger.debug(f"No remaining rounds for match: {player1} vs {player2}")

                match_data.append(match_info)

            except Exception as match_error:
                logger.warning(f"Error parsing match: {match_error}")
                continue

    except Exception as e:
        logger.error(f"Failed to fetch or parse match data: {e}")

    logger.info(f"Extracted {len(match_data)} matches.")
    return match_data
