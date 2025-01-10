from playwright.sync_api import sync_playwright

def fetch_all_matches(url):
    """
    Fetch details and odds for all matches on the page.
    Args:
        url (str): URL of the OddsPortal Eredivisie page.

    Returns:
        list: List of dictionaries containing match details (team names, odds).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to the page...")
        page.goto(url)

        try:
            # Wait for the parent container of matches
            page.wait_for_selector('div[data-v-b8d70024] > div[id]', timeout=60000)

            # Locate all match containers
            match_containers = page.locator('div[data-v-b8d70024] > div[id]')
            match_count = match_containers.count()
            print(f"Found {match_count} match containers.")

            all_matches = []
            processed_ids = set()  # To track unique match rows

            for i in range(match_count):
                try:
                    # Scope to the current match container
                    container = match_containers.nth(i)
                    row_id = container.get_attribute("id")

                    # Skip duplicates
                    if row_id in processed_ids:
                        print(f"Skipping duplicate row with ID {row_id}")
                        continue
                    processed_ids.add(row_id)

                    # Extract team names
                    home_team = container.locator('a[title]').nth(0).text_content().strip()
                    away_team = container.locator('a[title]').nth(1).text_content().strip()

                    # Extract odds
                    odds = container.locator('div[data-v-34474325] p')
                    home_odd = odds.nth(0).text_content().strip()
                    draw_odd = odds.nth(1).text_content().strip()
                    away_odd = odds.nth(2).text_content().strip()

                    # Add match details to the list
                    all_matches.append({
                        "home_team": home_team,
                        "away_team": away_team,
                        "odds": {
                            "home": home_odd,
                            "draw": draw_odd,
                            "away": away_odd
                        }
                    })
                except Exception as e:
                    print(f"Error processing match {i + 1}: {e}")
                    continue

            browser.close()
            return all_matches

        except Exception as e:
            print(f"Error fetching matches: {e}")
            browser.close()
            return None

def display_all_matches(matches):
    """Display all match data in the terminal."""
    if matches:
        print("\nAll Matches:")
        for idx, match in enumerate(matches):
            print(f"\nMatch {idx + 1}:")
            print(f"Teams: {match['home_team']} vs {match['away_team']}")
            print(f"Odds: Home {match['odds']['home']}, Draw {match['odds']['draw']}, Away {match['odds']['away']}")
    else:
        print("No match data available.")

if __name__ == "__main__":
    url = "https://www.oddsportal.com/soccer/netherlands/eredivisie/"
    print("Fetching all match details...")
    all_matches = fetch_all_matches(url)

    display_all_matches(all_matches)
