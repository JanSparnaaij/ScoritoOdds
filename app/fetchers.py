from app.player_ratings import PLAYER_RATINGS
from flask import current_app
import asyncio
from app.browser import get_browser
from flask import current_app

async def fetch_football_matches_async(league_url):
    """
    Asynchronously fetch match details and odds for a specific league.

    Args:
        league_url (str): URL of the league page on OddsPortal.

    Returns:
        list: List of dictionaries containing match details (team names, odds).
    """
    app = current_app._get_current_object()
    browser = await get_browser(app)
    try:
        page = await browser.new_page()

        app.logger.info(f"Navigating to league: {league_url}")
        await page.goto(league_url, timeout=30000)
        app.logger.info("League page loaded successfully!")

        # Validate that the correct page is loaded
        if "football" not in page.url:
            app.logger.warning(f"Failed to navigate to the league. Redirected to: {page.url}")
            return []

        # Wait for the parent container of matches
        await page.wait_for_selector('div[data-v-b8d70024] > div.eventRow', timeout=30000)

        # Locate all match containers
        match_containers = page.locator('div[data-v-b8d70024] > div.eventRow')
        match_count = await match_containers.count()
        app.logger.info(f"Found {match_count} match containers.")

        all_matches = []
        processed_ids = set()  # To track unique match rows

        for i in range(match_count):
            try:
                # Scope to the current match container
                container = match_containers.nth(i)
                row_id = await container.get_attribute("id")

                # Skip duplicates
                if row_id in processed_ids:
                    app.logger.info(f"Skipping duplicate row with ID {row_id}")
                    continue
                processed_ids.add(row_id)

                # Extract team names
                home_team_locator = container.locator('a[title]').nth(0)
                away_team_locator = container.locator('a[title]').nth(1)

                if not await home_team_locator.is_visible() or not await away_team_locator.is_visible():
                    print(f"Skipping incomplete match data for row {row_id}")
                    continue

                home_team = await home_team_locator.text_content()
                away_team = await away_team_locator.text_content()

                # Extract odds
                odds = container.locator('div[data-v-34474325] p')                   
                home_odd = await odds.nth(0).text_content(timeout=5000)
                draw_odd = await odds.nth(1).text_content(timeout=5000)
                away_odd = await odds.nth(2).text_content(timeout=5000)

                # Add match details to the list
                all_matches.append({
                    "home_team": home_team.strip(),
                    "away_team": away_team.strip(),
                    "odds": {
                        "home": home_odd.strip(),
                        "draw": draw_odd.strip(),
                        "away": away_odd.strip(),
                    }
                })
            except Exception as e:
                app.logger.error(f"Error processing match {i + 1}: {e}")
                continue

        return all_matches
    except Exception as e:
        app.logger.error(f"Error fetching matches: {e}")
        return []

async def fetch_tennis_matches_async(league_url):
    """
    Fetch tennis match details asynchronously from OddsPortal.

    Args:
        league_url (str): The URL of the tennis league page.

    Returns:
        list: List of dictionaries containing match details and odds.
    """
    app = current_app._get_current_object()
    browser = await get_browser(app)  # Use the shared browser instance
    all_matches = []

    try:
        page = await browser.new_page()
        app.logger.info(f"Navigating to league: {league_url}")
        await page.goto(league_url, timeout=30000)
        app.logger.info("League page loaded successfully!")

        # Wait for match containers to load
        await page.wait_for_selector('div[data-v-b8d70024] > div.eventRow', timeout=30000)
        match_containers = page.locator('div[data-v-b8d70024] > div.eventRow')
        match_count = await match_containers.count()
        app.logger.info(f"Found {match_count} match containers.")

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
                app.logger.error(f"Error processing match {i + 1}: {e}")
                continue

        app.logger.info(f"Extracted {len(all_matches)} matches.")
        return all_matches

    except Exception as e:
        app.logger.error(f"Error fetching tennis matches: {e}")
        return all_matches  # Return whatever was fetched even if incomplete

    finally:
        if page:
            await page.close()  # Ensure the page is closed

def fetch_combined_tennis_data(matches_url, rounds_url):
    """
    Fetch tennis matches synchronously using the async fetcher.

    Args:
        matches_url (str): Matches URL.
        rounds_url (str): Rounds URL (not currently used).

    Returns:
        list: Match details.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a task for the coroutine to avoid nested asyncio.run issues
            return asyncio.ensure_future(fetch_tennis_matches_async(matches_url))
        else:
            # Run the coroutine directly if no loop is running
            return asyncio.run(fetch_tennis_matches_async(matches_url))
    except Exception as e:
        print(f"Error fetching combined tennis data: {e}")
        return []

def fetch_combined_tennis_data(matches_url, rounds_url):
    """
    Fetch tennis matches synchronously using the async fetcher.

    Args:
        matches_url (str): Matches URL.
        rounds_url (str): Rounds URL (not currently used).

    Returns:
        list: Match details.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a task for the coroutine to avoid nested asyncio.run issues
            future = asyncio.ensure_future(fetch_tennis_matches_async(matches_url))
            return loop.run_until_complete(future)
        else:
            # Run the coroutine directly if no loop is running
            return asyncio.run(fetch_tennis_matches_async(matches_url))
    except Exception as e:
        print(f"Error fetching combined tennis data: {e}")
        return []