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
        logger.info(f"Fetching round data from: {rounds_url}")
        rounds_response = requests.get(rounds_url)
        rounds_response.raise_for_status()
        rounds_soup = BeautifulSoup(rounds_response.content, "html.parser")

        # Update selector for rounds
        rounds = rounds_soup.select(".round-name-selector")  # Adjust selector as needed
        round_names = [round_.text.strip() for round_ in rounds if round_.text]
        logger.info(f"Extracted rounds: {round_names}")
    except Exception as e:
        logger.error(f"Failed to fetch or parse round data: {e}")
        round_names = []

    try:
        # Fetch match data
        logger.info(f"Fetching match data from: {matches_url}")
        matches_response = requests.get(matches_url)
        matches_response.raise_for_status()
        matches_soup = BeautifulSoup(matches_response.content, "html.parser")

        # Update selector for match containers
        match_containers = matches_soup.select("div[data-v-b8d70024] .group.flex")  # Adjust selector
        logger.info(f"Found {len(match_containers)} match containers.")

        for container in match_containers:
            try:
                # Player names
                player1 = container.select_one("a[title]").get("title").strip()
                player2 = container.select("a[title]")[-1].get("title").strip()

                # Odds
                odds = container.select("div[data-v-34474325] p")
                if len(odds) < 2:
                    logger.warning(f"Skipping match due to missing odds.")
                    continue
                odds_player1 = float(odds[0].text.strip())
                odds_player2 = float(odds[1].text.strip())

                # Calculate expected points
                expected_points_player1 = round(100 / odds_player1, 2)
                expected_points_player2 = round(100 / odds_player2, 2)

                # Date (if available)
                date_element = container.select_one("p[data-v-931a4162]")
                match_date = date_element.text.strip() if date_element else "Unknown"

                # Assign round if available
                match_round = round_names.pop(0) if round_names else "Unknown"

                # Add match details to list
                match_data.append({
                    "date": match_date,
                    "round": match_round,
                    "players": {
                        "player1": player1,
                        "player2": player2,
                    },
                    "categories": {
                        "player1": PLAYER_RATINGS.get(player1, "Unknown"),
                        "player2": PLAYER_RATINGS.get(player2, "Unknown"),
                    },
                    "odds": {
                        "player1": odds_player1,
                        "player2": odds_player2,
                    },
                    "expected_points": {
                        "player1": expected_points_player1,
                        "player2": expected_points_player2,
                    }
                })

            except Exception as e:
                logger.warning(f"Error processing match container: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to fetch or parse match data: {e}")

    return match_data
