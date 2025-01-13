from app.player_ratings import PLAYER_RATINGS
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def fetch_html_content(url):
    """
    Fetch HTML content from the given URL using async Playwright.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            print(f"Fetching content from: {url}")
            await page.goto(url, timeout=20000)
            html_content = await page.content()
            return html_content
        except Exception as e:
            print(f"Error fetching content: {e}")
            return None
        finally:
            await browser.close()


def parse_tennis_rounds(html_content):
    """
    Parse tennis rounds from HTML content using BeautifulSoup.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    rounds = []
    for round_div in soup.select('div.round'):
        round_name = round_div.get('class', [])[1] if len(round_div.get('class', [])) > 1 else "Unknown"
        for match_div in round_div.select('div.match'):
            try:
                player1 = match_div.select_one('span.participant.home .name').text.strip()
                player2 = match_div.select_one('span.participant.away .name').text.strip()
                date = match_div.select_one('span.date').text.strip()
                rounds.append({'round': round_name, 'player1': player1, 'player2': player2, 'date': date})
            except Exception as e:
                print(f"Error parsing round match: {e}")
    return rounds


def parse_tennis_matches(html_content):
    """
    Parse tennis matches from HTML content using BeautifulSoup and include player ratings.
    """
    def calculate_win_probability(odd):
        return 1 / odd

    def get_points_for_rating(rating):
        return {"A": 20, "B": 40, "C": 60, "D": 90}.get(rating, 0)

    soup = BeautifulSoup(html_content, 'html.parser')
    matches = []
    for match_div in soup.select('div[data-v-b8d70024] > div[id]'):
        try:
            player1 = match_div.select_one('a[title]').text.strip()
            player2 = match_div.select('a[title]')[1].text.strip()
            odds = [float(od.text.strip()) for od in match_div.select('div[data-v-34474325] p')]

            if len(odds) < 2:
                print(f"Skipping match due to missing odds.")
                continue

            # Calculate probabilities
            player1_prob = calculate_win_probability(odds[0])
            player2_prob = calculate_win_probability(odds[1])
            total_prob = player1_prob + player2_prob
            player1_prob /= total_prob
            player2_prob /= total_prob

            # Get player ratings
            player1_rating = PLAYER_RATINGS.get(player1, "X")
            player2_rating = PLAYER_RATINGS.get(player2, "X")

            # Calculate expected points
            player1_expected_points = round(player1_prob * get_points_for_rating(player1_rating), 2)
            player2_expected_points = round(player2_prob * get_points_for_rating(player2_rating), 2)

            matches.append({
                "players": {"player1": player1, "player2": player2},
                "odds": {"player1": odds[0], "player2": odds[1]},
                "probabilities": {"player1": round(player1_prob * 100, 2), "player2": round(player2_prob * 100, 2)},
                "expected_points": {"player1": player1_expected_points, "player2": player2_expected_points},
                "ratings": {"player1": player1_rating, "player2": player2_rating},
            })
        except Exception as e:
            print(f"Error parsing match: {e}")
    return matches


async def fetch_combined_tennis_data(matches_url, rounds_url):
    """
    Fetch and parse combined tennis data asynchronously.
    """
    rounds_html = await fetch_html_content(rounds_url)
    matches_html = await fetch_html_content(matches_url)

    rounds = parse_tennis_rounds(rounds_html) if rounds_html else []
    matches = parse_tennis_matches(matches_html) if matches_html else []

    # Merge rounds into matches
    for match in matches:
        for round_match in rounds:
            if (
                match["players"]["player1"] == round_match["player1"]
                and match["players"]["player2"] == round_match["player2"]
                and match.get("date") == round_match.get("date")
            ):
                match["round"] = round_match["round"]
                match["date"] = round_match["date"]
                break
        else:
            match["round"] = "Unknown"
            match["date"] = "Unknown"

    return matches
