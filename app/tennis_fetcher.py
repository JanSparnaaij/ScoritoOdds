from playwright.sync_api import sync_playwright

def fetch_tennis_matches(url, PLAYER_RATINGS):
    """
    Fetch details, ratings, and expected points for tennis matches on the page.
    Args:
        url (str): URL of the tennis page.

    Returns:
        list: List of dictionaries containing match details (datetime, players, odds, ratings, and expected points).
    """
    def calculate_win_probability(odd):
        """Calculate win probability based on a single odd."""
        return 1 / odd

    def get_points_for_rating(rating):
        """Get points based on player rating."""
        return {"A": 10, "B": 20, "C": 30, "D": 60, "X": 0}.get(rating, 0)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating to the page: {url}")
        page.goto(url)

        try:
            # Wait for match rows to load
            page.wait_for_selector('div[data-v-b8d70024] > div[id]', timeout=60000)

            # Lazy-load all matches by scrolling to the bottom
            previous_count = -1
            while True:
                match_containers = page.locator('div[data-v-b8d70024] > div[id]')
                current_count = match_containers.count()

                if current_count == previous_count:
                    # No new matches are being loaded
                    break

                print(f"Loaded {current_count} matches so far. Scrolling...")
                previous_count = current_count
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)  # Allow time for lazy loading

            print(f"Final match count: {current_count}")

            tennis_matches = []
            current_round = None  # To store the current round for a group of matches
            current_date = None  # To store the date for the current group of matches

            for i in range(current_count):
                try:
                    # Scope to the current match container
                    container = match_containers.nth(i)

                    # Check if this container specifies a new round
                    round_element = container.locator('div.round-class')  # Replace 'round-class' with the actual class for round
                    if round_element.count() > 0:
                        current_round = round_element.text_content().strip()


                    # Check if this container specifies a new date
                    date_element = container.locator('div.bg-gray-light div.text-black-main')
                    if date_element.count() > 0:
                        current_date = date_element.text_content().strip()

                    # Ensure both round and date are available for matches
                    if not current_round or not current_date:
                        print(f"Skipping match {i + 1}: No round or date found.")
                        continue

                    # Extract time (e.g., "01:00")
                    match_time = container.locator('p[data-v-931a4162]').text_content().strip()

                    # Combine date and time into datetime
                    datetime = f"{current_date} {match_time}"

                    # Extract player names
                    player1 = container.locator('a[title]').nth(0).text_content().strip()
                    player2 = container.locator('a[title]').nth(1).text_content().strip()

                    # Extract odds
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
                    player1_rating = PLAYER_RATINGS.get(player1, "X")
                    player2_rating = PLAYER_RATINGS.get(player2, "X")

                    # Calculate expected points
                    player1_expected_points = round(player1_prob * get_points_for_rating(player1_rating), 2)
                    player2_expected_points = round(player2_prob * get_points_for_rating(player2_rating), 2)

                    # Add match details to the list
                    tennis_matches.append({
                        "datetime": datetime,
                        "round": current_round,
                        "players": {
                            "player1": player1,
                            "player1_rating": player1_rating,
                            "player2": player2,
                            "player2_rating": player2_rating,
                        },
                        "odds": {
                            "player1": player1_odd,
                            "player2": player2_odd,
                        },
                        "expected_points": {
                            "player1": player1_expected_points,
                            "player2": player2_expected_points,
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
