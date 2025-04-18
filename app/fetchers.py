from app.player_ratings import PLAYER_RATINGS
from flask import current_app
from app.browser import get_browser
from flask import current_app
from datetime import datetime, timedelta
from app.constants import AUSTRALIAN_OPEN_SCHEDULE

async def fetch_football_matches_async(league_url):
    """
    Asynchronously fetch match details and odds for a specific league.

    Args:
        league_url (str): URL of the league page on OddsPortal.

    Returns:
        list: List of dictionaries containing match details (team names, odds, date).
    """
    app = current_app._get_current_object()
    browser = await get_browser(app)
    all_matches = []
    current_date = None
    seen_matches = set()

    try:
        page = await browser.new_page()
        app.logger.info(f"Navigating to league: {league_url}")
        await page.goto(league_url, timeout=30000)
        app.logger.info("League page loaded successfully!")

        # Wait for the match container rows
        await page.wait_for_selector('div[data-v-b8d70024]', timeout=30000)
        rows = page.locator('div[data-v-b8d70024]')
        row_count = await rows.count()
        app.logger.info(f"Found {row_count} rows.")

        for i in range(row_count):
            try:
                row = rows.nth(i)

                # Check if the row contains a date
                if await row.locator('.text-black-main.font-main').count() > 0:
                    date_text = (await row.locator('.text-black-main.font-main').first.text_content(timeout=1000)).strip()
                    app.logger.debug(f"Extracted date text: {date_text}")

                    # Handle "Today," "Tomorrow," or explicit dates
                    if "Today" in date_text:
                        current_date = datetime.now().strftime("%d-%m-%Y")
                    elif "Tomorrow" in date_text:
                        current_date = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
                    else:
                        try:
                            # Parse full dates or add the current year dynamically
                            cleaned_date_text = date_text.split(",")[-1].strip()
                            if len(cleaned_date_text.split()) == 2:  # e.g., "28 Jan"
                                current_year = datetime.now().year
                                cleaned_date_text += f" {current_year}"
                            current_date = datetime.strptime(cleaned_date_text, "%d %b %Y").strftime("%d-%m-%Y")
                        except ValueError as e:
                            app.logger.error(f"Error parsing date: {date_text}, {e}")
                            current_date = "Unknown"

                    app.logger.debug(f"Set current_date to: {current_date}")
                    continue  # Move to the next row

                # Check if the row contains match data
                if await row.locator('a[title]').count() > 0:
                    home_team = await row.locator('a[title]').nth(0).text_content(timeout=1000)
                    away_team = await row.locator('a[title]').nth(1).text_content(timeout=1000)

                    # Create a unique match identifier
                    match_id = f"{home_team.strip()} vs {away_team.strip()}"
                    if match_id in seen_matches:
                        app.logger.debug(f"Duplicate match found: {match_id}")
                        continue
                    seen_matches.add(match_id)

                    # Extract odds
                    odds = row.locator('div[data-v-34474325] p')
                    if await odds.count() < 3:
                        app.logger.warning(f"Skipping row at index {i}: Missing odds.")
                        continue

                    home_odd = await odds.nth(0).text_content(timeout=1000)
                    draw_odd = await odds.nth(1).text_content(timeout=1000)
                    away_odd = await odds.nth(2).text_content(timeout=1000)

                    # Add match details to the list
                    match_data = {
                        "date": current_date or "Unknown",
                        "home_team": home_team.strip(),
                        "away_team": away_team.strip(),
                        "odds": {
                            "home": home_odd.strip(),
                            "draw": draw_odd.strip(),
                            "away": away_odd.strip(),
                        },
                    }
                    all_matches.append(match_data)
                    app.logger.debug(f"Added match: {home_team.strip()} vs {away_team.strip()} on {current_date}")

            except Exception as e:
                app.logger.error(f"Error processing row at index {i}: {e}")
                continue

        app.logger.info(f"Extracted {len(all_matches)} matches.")
        return all_matches

    except Exception as e:
        app.logger.error(f"Error fetching matches: {e}")
        return []

def determine_round(match_date: str) -> str:
    """
    Determine the round of the Australian Open based on the match date.

    Args:
        match_date (str): The match date in the format "YYYY-MM-DD".

    Returns:
        str: The corresponding round name, or "Unknown" if no match is found.
    """
    try:
        match_date_obj = datetime.strptime(match_date, "%Y-%m-%d")
        for round_name, dates in AUSTRALIAN_OPEN_SCHEDULE.items():
            start_date = datetime.strptime(dates["start"], "%Y-%m-%d")
            end_date = datetime.strptime(dates["end"], "%Y-%m-%d")
            if start_date <= match_date_obj <= end_date:
                return round_name
        return "Unknown"
    except ValueError:
        return "Unknown"  # Handle invalid date formats
    
import re

def contains_score(name):
    """
    Check if the player name contains a score (e.g., "6-4", "7-6").
    
    Args:
        player_name (str): The name to check.
        
    Returns:
        bool: True if the name contains a score, False otherwise.
    """
    return bool(re.search(r'\d', name))

async def fetch_tennis_matches_async(league_url):
    """
    Fetch tennis match details asynchronously from OddsPortal.

    Args:
        league_url (str): The URL of the tennis league page.

    Returns:
        list: List of dictionaries containing match details, odds, and date.
    """
    app = current_app._get_current_object()
    browser = await get_browser(app)  # Use the shared browser instance
    all_matches = []
    current_date = None
    seen_matches = set()

    # Points per round
    ROUND_POINTS = {
        "Quarterfinals": [240, 400, 560, 720],
        "Semifinals": [320, 480, 640, 800],
        "Finals": [400, 560, 720, 800],
    }

    try:
        page = await browser.new_page()
        app.logger.info(f"Navigating to league: {league_url}")
        await page.goto(league_url, timeout=30000)
        app.logger.info("League page loaded successfully!")

        # Wait for the match container rows
        await page.wait_for_selector('div[data-v-b8d70024]', timeout=30000)
        rows = page.locator('div[data-v-b8d70024]')
        row_count = await rows.count()
        app.logger.info(f"Found {row_count} rows.")

        for i in range(row_count):
            row = rows.nth(i)
            try:
                # Check if the row contains a date
                if await row.locator('.text-black-main.font-main').count() > 0:
                    # Extract the current date
                    date_text = (await row.locator('.text-black-main.font-main').first.text_content(timeout=1000)).strip()
                    app.logger.debug(f"Extracted date text: {date_text}")

                    # Remove prefixes like "Today" or "Tomorrow" if present
                    if "Today" in date_text:
                        current_date = datetime.now().strftime("%d-%m-%Y")
                    elif "Tomorrow" in date_text:
                        current_date = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
                    else:
                        # Parse and reformat the date
                        try:
                            current_date = datetime.strptime(date_text, "%d %b %Y").strftime("%d-%m-%Y")
                        except ValueError as e:
                            app.logger.error(f"Error parsing date: {date_text}, {e}")
                            current_date = "Unknown"
                    continue  # Skip processing further as this is a date row
                    
                # Check if the row contains match data
                if await row.locator('a[title]').count() > 0:
                    # Extract player names
                    home_player = await row.locator('a[title]').nth(0).text_content(timeout=1000)
                    away_player = await row.locator('a[title]').nth(1).text_content(timeout=1000)

                    # Check if names contain scores and skip them if they do
                    if contains_score(home_player) or contains_score(away_player):
                        app.logger.debug(f"Skipping match with score in names: {home_player} vs {away_player}")
                        continue

                    # Create a unique identifier for deduplication
                    match_id = f"{home_player.strip()} vs {away_player.strip()}"
                    if match_id in seen_matches:
                        app.logger.debug(f"Duplicate match found: {match_id}")
                        continue
                    seen_matches.add(match_id)

                    # Extract odds
                    odds = row.locator('div[data-v-34474325] p')
                    home_odd = float(await odds.nth(0).text_content(timeout=1000))
                    away_odd = float(await odds.nth(1).text_content(timeout=1000))

                    # Determine the round based on the current date
                    if current_date and current_date != "Unknown":
                        round_name = determine_round(datetime.strptime(current_date, "%d-%m-%Y").strftime("%Y-%m-%d"))
                    else:
                        round_name = "Unknown"

                    # Category and points calculations
                    home_category = PLAYER_RATINGS.get(home_player, "Unknown")
                    away_category = PLAYER_RATINGS.get(away_player, "Unknown")
                    round_specific_points = ROUND_POINTS.get(round_name, "Unknown")
                    home_points = round_specific_points[0] if home_category == "A" else \
                                  round_specific_points[1] if home_category == "B" else \
                                  round_specific_points[2] if home_category == "C" else \
                                  round_specific_points[3]
                    away_points = round_specific_points[0] if away_category == "A" else \
                                  round_specific_points[1] if away_category == "B" else \
                                  round_specific_points[2] if away_category == "C" else \
                                  round_specific_points[3]
                    home_win_probability = round(100 / home_odd, 2)
                    away_win_probability = round(100 / away_odd, 2)
                    expected_home_point = round(home_win_probability * home_points / 100, 2)
                    expected_away_point = round(away_win_probability * away_points / 100, 2)

                    # Construct match data
                    match_data = {
                        "date": current_date or "Unknown",
                        "round": round_name,
                        "home_player": home_player.strip(),
                        "away_player": away_player.strip(),
                        "odds": {
                            "home": home_odd,
                            "away": away_odd,
                        },
                        "expected_points": {
                            "home": expected_home_point,
                            "away": expected_away_point,
                        },
                        "categories": {
                            "player1": home_category,
                            "player2": away_category,
                        },
                    }
                    all_matches.append(match_data)
            except Exception as e:
                app.logger.error(f"Error processing row {i + 1}: {e}")
                continue

        app.logger.info(f"Extracted {len(all_matches)} matches.")
        return all_matches  # Moved outside the loop

    except Exception as e:
        app.logger.error(f"Error fetching tennis matches: {e}")
        return all_matches  # Return whatever was fetched even if incomplete

    finally:
        if page:
            await page.close()  # Ensure the page is closed

async def fetch_combined_tennis_data(matches_url: str, rounds_url: str) -> list:
    """
    Fetch tennis matches synchronously using the async fetcher.

    Args:
        matches_url (str): Matches URL.
        rounds_url (str): Rounds URL (not currently used).

    Returns:
        list: Match details.
    """
    try:
        data = await fetch_tennis_matches_async(matches_url)
        if not data:
            print(f"No data fetched from: {matches_url}")
        else:
            print(f"Fetched {len(data)} matches from: {matches_url}")
        return data
    except Exception as e:
        print(f"Error fetching combined tennis data: {e}")
        return []
