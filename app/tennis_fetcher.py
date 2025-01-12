from playwright.sync_api import sync_playwright
from app.player_ratings import PLAYER_RATINGS

def fetch_tennis_rounds(rounds_url):
    """
    Fetch rounds from the standings page.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Fetching rounds from: {rounds_url}")
        page.goto(rounds_url)

        try:
            # Wait for the rounds table to load
            page.wait_for_selector('table.standings', timeout=60000)
            round_rows = page.locator('table.standings > tbody > tr')

            rounds = {}
            for i in range(round_rows.count()):
                try:
                    row = round_rows.nth(i)
                    round_name = row.locator('td.round-column').text_content().strip()
                    player1 = row.locator('td.player1-column').text_content().strip()
                    player2 = row.locator('td.player2-column').text_content().strip()

                    # Store rounds by match key
                    match_key = f"{player1} vs {player2}"
                    rounds[match_key] = round_name
                except Exception as e:
                    print(f"Error extracting round {i + 1}: {e}")
                    continue

            browser.close()
            return rounds

        except Exception as e:
            print(f"Error fetching rounds: {e}")
            browser.close()
            return {}

def fetch_tennis_matches(matches_url):
    """
    Fetch matches and their details from the main matches page.
    """
    def calculate_win_probability(odd):
        """Calculate win probability based on a single odd."""
        return 1 / odd

    def get_points_for_rating(rating):
        """Get points based on player rating."""
        return {"A": 10, "B": 20, "C": 30, "D": 60}.get(rating, 0)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Fetching matches from: {matches_url}")
        page.goto(matches_url)

        try:
            # Wait for matches to load
            page.wait_for_selector('div[data-v-b8d70024] > div[id]', timeout=60000)

            # Scroll to load all matches
            previous_count = -1
            while True:
                match_containers = page.locator('div[data-v-b8d70024] > div[id]')
                current_count = match_containers.count()

                if current_count == previous_count:
                    break

                print(f"Loaded {current_count} matches so far. Scrolling...")
                previous_count = current_count
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

            print(f"Final match count: {current_count}")
            matches = []

            for i in range(current_count):
                try:
                    container = match_containers.nth(i)

                    # Extract match details
                    player1 = container.locator('a[title]').nth(0).text_content().strip()
                    player2 = container.locator('a[title]').nth(1).text_content().strip()
                    match_key = f"{player1} vs {player2}"

                    odds = container.locator('div[data-v-34474325] p')
                    player1_odd = float(odds.nth(0).text_content().strip())
                    player2_odd = float(odds.nth(1).text_content().strip())

                    # Calculate win probabilities
                    player1_prob = calculate_win_probability(player1_odd)
                    player2_prob = calculate_win_probability(player2_odd)

                    # Normalize probabilities
                    total_prob = player1_prob + player2_prob
                    player1_prob /= total_prob
                    player2_prob /= total_prob

                    # Get player ratings
                    player1_rating = PLAYER_RATINGS.get(player1, "X")  # Default to "X" if rating is missing
                    player2_rating = PLAYER_RATINGS.get(player2, "X")

                    # Calculate expected points
                    player1_expected_points = round(player1_prob * get_points_for_rating(player1_rating), 2)
                    player2_expected_points = round(player2_prob * get_points_for_rating(player2_rating), 2)

                    matches.append({
                        "match_key": match_key,
                        "players": {
                            "player1": player1,
                            "player2": player2,
                        },
                        "odds": {
                            "player1": player1_odd,
                            "player2": player2_odd,
                        },
                        "probabilities": {
                            "player1": round(player1_prob * 100, 2),
                            "player2": round(player2_prob * 100, 2),
                        },
                        "expected_points": {
                            "player1": player1_expected_points,
                            "player2": player2_expected_points,
                        },
                        "ratings": {
                            "player1": player1_rating,
                            "player2": player2_rating,
                        }
                    })
                except Exception as e:
                    print(f"Error processing match {i + 1}: {e}")
                    continue

            browser.close()
            return matches

        except Exception as e:
            print(f"Error fetching matches: {e}")
            browser.close()
            return []

def fetch_combined_tennis_data(matches_url, rounds_url):
    """
    Fetch combined tennis data with rounds, matches, and other details.
    """
    # Fetch rounds and matches
    rounds = fetch_tennis_rounds(rounds_url)
    matches = fetch_tennis_matches(matches_url)

    # Merge rounds into matches
    for match in matches:
        match_key = match["match_key"]
        match["round"] = rounds.get(match_key, "Unknown")  # Default to "Unknown" if round not found

    return matches

if __name__ == "__main__":
    matches_url = "https://example.com/matches"
    rounds_url = "https://example.com/rounds"

    combined_data = fetch_combined_tennis_data(matches_url, rounds_url)
    print(combined_data)
