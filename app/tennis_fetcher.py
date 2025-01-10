from playwright.sync_api import sync_playwright

def fetch_tennis_matches(url):
    """
    Fetch details and odds for tennis matches on the page.
    Args:
        url (str): URL of the tennis page.

    Returns:
        list: List of dictionaries containing match details (datetime, players, odds).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating to the page: {url}")
        page.goto(url)

        try:
            # Wait for match rows to load
            page.wait_for_selector('div[data-v-b8d70024] > div[id]', timeout=60000)

            # Locate all match containers
            match_containers = page.locator('div[data-v-b8d70024] > div[id]')
            match_count = match_containers.count()
            print(f"Found {match_count} tennis matches.")

            tennis_matches = []
            current_date = None  # To store the date for the current group of matches

            for i in range(match_count):
                try:
                    # Scope to the current match container
                    container = match_containers.nth(i)

                    # Check if this container specifies a new date
                    date_element = container.locator('div.bg-gray-light div.text-black-main')
                    if date_element.count() > 0:
                        current_date = date_element.text_content().strip()

                    # Ensure a date is available for matches
                    if not current_date:
                        print(f"Skipping match {i + 1}: No date found.")
                        continue

                    # Extract time (e.g., "01:00")
                    match_time = container.locator('p[data-v-931a4162]').text_content().strip()

                    # Combine date and time into datetime
                    datetime = f"{current_date} {match_time}"

                    # Extract player names
                    player1 = container.locator('a[title]').nth(0).get_attribute('title').strip()
                    player2 = container.locator('a[title]').nth(1).get_attribute('title').strip()

                    # Extract odds
                    odds = container.locator('div[data-v-34474325] p')
                    player1_odd = odds.nth(0).text_content().strip()
                    player2_odd = odds.nth(1).text_content().strip()

                    # Add match details to the list
                    tennis_matches.append({
                        "datetime": datetime,
                        "players": {
                            "player1": player1,
                            "player2": player2
                        },
                        "odds": {
                            "player1": player1_odd,
                            "player2": player2_odd
                        }
                    })
                except Exception as e:
                    print(f"Error processing match {i + 1}: {e}")
                    continue

            browser.close()
            return tennis_matches

        except Exception as e:
            print(f"Error fetching matches: {e}")
            browser.close()
            return []
