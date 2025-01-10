from playwright.sync_api import sync_playwright

def extract_player_names(url):
    """
    Extract player names from the specified OddsPortal page using Playwright.
    
    Args:
        url (str): URL of the OddsPortal page.
    
    Returns:
        set: A set of unique player names.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating to the page: {url}")
        page.goto(url)

        # Wait for the page to load and start lazy loading matches
        page.wait_for_selector('div[data-v-b8d70024] > div[id]', timeout=60000)

        player_names = set()
        previous_count = -1

        while True:
            # Locate all match containers
            match_containers = page.locator('div[data-v-b8d70024] > div[id]')
            current_count = match_containers.count()

            if current_count == previous_count:
                # No new matches are being loaded
                break

            print(f"Loaded {current_count} match containers so far. Scrolling...")
            previous_count = current_count

            # Extract player names from currently loaded matches
            for i in range(current_count):
                try:
                    # Scope to the current match container
                    container = match_containers.nth(i)

                    # Extract player names
                    players = container.locator('a[title]')
                    for j in range(players.count()):
                        player_name = players.nth(j).get_attribute('title').strip()
                        player_names.add(player_name)
                except Exception as e:
                    print(f"Error processing match {i + 1}: {e}")
                    continue

            # Scroll to load more matches
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)  # Allow time for lazy loading

        browser.close()
        return player_names


# Example usage
if __name__ == "__main__":
    url = "https://www.oddsportal.com/tennis/australia/atp-australian-open/"
    players = extract_player_names(url)
    print("Players found:")
    for player in sorted(players):
        print(player)
