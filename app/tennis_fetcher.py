from playwright.async_api import async_playwright
from app.player_ratings import PLAYER_RATINGS
import asyncio

async def fetch_tennis_matches_async(league_url):
    """
    Fetch tennis match details asynchronously from OddsPortal.

    Args:
        league_url (str): The URL of the tennis league page.

    Returns:
        list: List of dictionaries containing match details and odds.
    """
    async with async_playwright() as p:
        browser = None
        try:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            print(f"Navigating to league: {league_url}")
            await page.goto(league_url, timeout=30000)
            print("League page loaded successfully!")

            # Wait for match containers to load
            await page.wait_for_selector('div[data-v-b8d70024] > div.eventRow', timeout=30000)
            match_containers = page.locator('div[data-v-b8d70024] > div.eventRow')
            match_count = await match_containers.count()

            print(f"Found {match_count} match containers.")
            all_matches = []

            for i in range(match_count):
                container = match_containers.nth(i)
                try:
                    # Extract player names and categories
                    home_player = await container.locator('a[title]').nth(0).text_content(timeout=5000)
                    away_player = await container.locator('a[title]').nth(1).text_content(timeout=5000)

                    # Extract odds
                    odds = container.locator('div[data-v-34474325] p')
                    home_odd = float(await odds.nth(0).text_content(timeout=5000))
                    away_odd = float(await odds.nth(1).text_content(timeout=5000))

                    # Calculate expected points
                    expected_home_point = round(100 / home_odd, 2)
                    expected_away_point = round(100 / away_odd, 2)

                    # Construct match data
                    match_data = {
                        "date": "Unknown",  # Placeholder for now
                        "round": "R?",  # Placeholder for round
                        "home_player": home_player.strip(),
                        "home_category": PLAYER_RATINGS.get(home_player.strip(), "Unknown"),
                        "away_player": away_player.strip(),
                        "away_category": PLAYER_RATINGS.get(away_player.strip(), "Unknown"),
                        "odds": {
                            "home": home_odd,
                            "away": away_odd,
                        },
                        "expected_points": {
                            "home": expected_home_point,
                            "away": expected_away_point,
                        }
                    }
                    all_matches.append(match_data)
                except Exception as e:
                    print(f"Error processing match {i + 1}: {e}")
                    continue

            print(f"Extracted {len(all_matches)} matches.")
            return all_matches

        except Exception as e:
            print(f"Error fetching tennis matches: {e}")
            return []

        finally:
            if browser:
                await browser.close()


def fetch_combined_tennis_data(matches_url, rounds_url):
    """
    Fetch tennis matches synchronously using the async fetcher.

    Args:
        matches_url (str): Matches URL.
        rounds_url (str): Rounds URL (placeholder).

    Returns:
        list: Match details.
    """
    try:
        return asyncio.run(fetch_tennis_matches_async(matches_url))
    except Exception as e:
        print(f"Error fetching combined tennis data: {e}")
        return []
