from app.player_ratings import PLAYER_RATINGS
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def fetch_tennis_rounds(rounds_url):
    """
    Fetch and parse tennis rounds from the standings page.
    """
    def parse_rounds(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        rounds = []

        # Parse round containers
        for round_div in soup.select('div.round'):
            round_name = "Unknown"
            if len(round_div.get('class', [])) > 1:
                round_name = round_div['class'][1]

            # Parse matches in this round
            for match_div in round_div.select('div.match'):
                try:
                    player1 = match_div.select_one('span.participant.home .name')
                    player2 = match_div.select_one('span.participant.away .name')
                    match_key = match_div.select_one('a.match-detail-link')
                    date = match_div.select_one('span.date')

                    player1_category = player1.select_one('span.codebook').text.strip() if player1.select_one(
                        'span.codebook') else "N/A"
                    player2_category = player2.select_one('span.codebook').text.strip() if player2.select_one(
                        'span.codebook') else "N/A"

                    if not all([player1, player2, match_key, date]):
                        continue

                    rounds.append({
                        'round': round_name,
                        'player1': player1.text.strip(),
                        'player2': player2.text.strip(),
                        'player1_category': player1_category,
                        'player2_category': player2_category,
                        'date': date.text.strip(),
                    })
                except Exception as e:
                    print(f"Error parsing match: {e}")
                    continue

        return rounds

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Fetching rounds from: {rounds_url}")
        page.goto(rounds_url)

        try:
            page.wait_for_selector('div.round', timeout=60000)
            html_content = page.content()
            rounds = parse_rounds(html_content)
            browser.close()
            return rounds
        except Exception as e:
            print(f"Error fetching rounds: {e}")
            browser.close()
            return []


def fetch_tennis_matches(matches_url):
    """
    Fetch matches and their details from the main matches page.
    """
    def calculate_win_probability(odd):
        return 1 / odd

    def get_points_for_rating(rating):
        return {"A": 10, "B": 20, "C": 30, "D": 60}.get(rating, 0)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Fetching matches from: {matches_url}")
        page.goto(matches_url)

        try:
            page.wait_for_selector('div[data-v-b8d70024] > div[id]', timeout=60000)
            match_containers = page.locator('div[data-v-b8d70024] > div[id]')
            matches = []

            for i in range(match_containers.count()):
                try:
                    container = match_containers.nth(i)
                    player1 = container.locator('a[title]').nth(0).text_content().strip()
                    player2 = container.locator('a[title]').nth(1).text_content().strip()

                    odds = container.locator('div[data-v-34474325] p')
                    player1_odd = float(odds.nth(0).text_content().strip())
                    player2_odd = float(odds.nth(1).text_content().strip())

                    player1_prob = calculate_win_probability(player1_odd)
                    player2_prob = calculate_win_probability(player2_odd)
                    total_prob = player1_prob + player2_prob
                    player1_prob /= total_prob
                    player2_prob /= total_prob

                    player1_rating = PLAYER_RATINGS.get(player1, "X")
                    player2_rating = PLAYER_RATINGS.get(player2, "X")

                    player1_expected_points = round(player1_prob * get_points_for_rating(player1_rating), 2)
                    player2_expected_points = round(player2_prob * get_points_for_rating(player2_rating), 2)

                    matches.append({
                        "match_key": f"{player1} vs {player2}",
                        "players": {"player1": player1, "player2": player2},
                        "odds": {"player1": player1_odd, "player2": player2_odd},
                        "probabilities": {"player1": round(player1_prob * 100, 2), "player2": round(player2_prob * 100, 2)},
                        "expected_points": {"player1": player1_expected_points, "player2": player2_expected_points},
                        "ratings": {"player1": player1_rating, "player2": player2_rating},
                    })
                except Exception as e:
                    print(f"Error processing match: {e}")
                    continue

            browser.close()
            return matches
        except Exception as e:
            print(f"Error fetching matches: {e}")
            browser.close()
            return []


def fetch_combined_tennis_data(matches_url, rounds_url, PLAYER_RATINGS):
    """
    Fetch combined tennis data with matches, rounds, and player categories.
    """
    # Fetch rounds and matches
    rounds = fetch_tennis_rounds(rounds_url)
    matches = fetch_tennis_matches(matches_url)

    # Merge rounds into matches
    for match in matches:
        for round_match in rounds:
            if (match["players"]["player1"] == round_match["player1"] and
                match["players"]["player2"] == round_match["player2"] and
                match.get("date") == round_match["date"]):
                match["round"] = round_match["round"]
                match["date"] = round_match["date"]
                match["categories"] = {
                    "player1": PLAYER_RATINGS.get(round_match["player1"], "N/A"),
                    "player2": PLAYER_RATINGS.get(round_match["player2"], "N/A"),
                }
                break
        else:
            match["round"] = "Unknown"
            match["categories"] = {
                "player1": PLAYER_RATINGS.get(match["players"]["player1"], "N/A"),
                "player2": PLAYER_RATINGS.get(match["players"]["player2"], "N/A"),
            }

    return matches


if __name__ == "__main__":
    matches_url = "https://example.com/matches"
    rounds_url = "https://www.oddsportal.com/tennis/australia/atp-australian-open/standings/"
    PLAYER_RATINGS = PLAYER_RATINGS
    combined_data = fetch_combined_tennis_data(matches_url, rounds_url, PLAYER_RATINGS)
    print(combined_data)
