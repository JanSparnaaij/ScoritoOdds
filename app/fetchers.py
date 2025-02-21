from app.player_ratings import PLAYER_RATINGS
from flask import current_app
from app.browser import get_browser
from datetime import datetime, timedelta
from app.constants import AUSTRALIAN_OPEN_SCHEDULE
from bs4 import BeautifulSoup
import asyncio
from typing import Dict, List, Optional
import requests

async def fetch_football_matches_async(url):
    """Fetch football matches from OddsPortal."""
    current_app.logger.info(f"Navigating to league: {url}")
    browser = await get_browser(current_app)
    page = await browser.new_page()
    
    try:
        # Navigate to the page
        await page.goto(url, wait_until="networkidle")
        current_app.logger.info("League page loaded successfully!")

        # Handle cookie consent if present
        try:
            current_app.logger.info("Looking for cookie consent button...")
            consent_button = await page.wait_for_selector("#onetrust-accept-btn-handler", timeout=5000)
            if consent_button:
                await consent_button.click()
                current_app.logger.info("Accepted cookies")
                await page.wait_for_timeout(2000)
        except Exception as e:
            current_app.logger.info(f"No cookie consent needed or error: {e}")

        # Wait for matches to load
        current_app.logger.info("Waiting for matches to appear...")
        await page.wait_for_selector(".border-black-borders.border-b", timeout=30000)
        
        # Extract matches
        matches = await page.evaluate("""() => {
            const matches = [];
            document.querySelectorAll('.border-black-borders.border-b').forEach(matchDiv => {
                try {
                    // Get team names
                    const homeTeam = matchDiv.querySelector('.participant-name')?.textContent.trim();
                    const awayTeam = matchDiv.querySelectorAll('.participant-name')[1]?.textContent.trim();
                    
                    // Get odds
                    const oddElements = matchDiv.querySelectorAll('[data-testid="add-to-coupon-button"] p');
                    const odds = Array.from(oddElements).map(odd => odd.textContent.trim());
                    
                    if (homeTeam && awayTeam && odds.length >= 3) {
                        matches.push({
                            home_team: homeTeam,
                            away_team: awayTeam,
                            home_odds: odds[0],
                            draw_odds: odds[1],
                            away_odds: odds[2]
                        });
                    }
                } catch (e) {
                    console.error('Error parsing match:', e);
                }
            });
            return matches;
        }""")

        current_app.logger.info(f"Found {len(matches)} matches")
        if len(matches) > 0:
            current_app.logger.info(f"Sample match: {matches[0]}")
        else:
            current_app.logger.warning("No matches found!")
            await page.screenshot(path="/app/debug/no_matches.png")
            
        return matches

    except Exception as e:
        current_app.logger.error(f"Error fetching matches: {e}")
        await page.screenshot(path="/app/debug/error.png")
        raise
    finally:
        await page.close()

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

async def fetch_cycling_startlist(url: str) -> Dict:
    """Fetch and parse cycling startlist from ProcyclingStats."""
    print(f"Fetching startlist from {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error response status: {response.status_code}")
            return {}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        teams_data = {}
        
        # Find the startlist container
        startlist = soup.find('ul', class_='startlist_v4')
        if not startlist:
            print("Could not find startlist container")
            return {}
            
        # Find all team entries
        teams = startlist.find_all('li')
        print(f"Found {len(teams)} teams")
        
        for team in teams:
            # Get team name from the team link
            team_link = team.find('a', class_='team')
            if team_link:
                team_name = team_link.text.strip()
                teams_data[team_name] = []
                print(f"Processing team: {team_name}")
                
                # Find riders list
                riders_list = team.find('ul')
                if riders_list:
                    riders = riders_list.find_all('li')
                    for rider in riders:
                        rider_link = rider.find('a')
                        if rider_link:
                            rider_name = rider_link.text.strip()
                            teams_data[team_name].append(rider_name)
                            print(f"Added rider: {rider_name}")
        
        print(f"Total teams processed: {len(teams_data)}")
        return teams_data
            
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return {}

async def fetch_all_cycling_data(races: Dict) -> Dict:
    """Fetch data for all cycling races."""
    tasks = []
    for race_id, race_info in races.items():
        task = asyncio.create_task(fetch_cycling_startlist(race_info['url']))
        tasks.append((race_id, task))
    
    results = {}
    for race_id, task in tasks:
        try:
            results[race_id] = await task
        except Exception as e:
            print(f"Error fetching {race_id}: {e}")
            results[race_id] = {}
    
    return results

def process_cycling_data(raw_data: Dict) -> Dict:
    """Process raw cycling data into a format suitable for the template."""
    all_teams = set()
    all_riders = {}
    
    # First pass: collect all teams and riders
    for race_data in raw_data.values():
        for team, riders in race_data.items():
            all_teams.add(team)
            for rider in riders:
                if rider not in all_riders:
                    all_riders[rider] = {'team': team, 'races': set()}  # Using set for collecting
    
    # Second pass: mark which races each rider is in
    for race_id, race_data in raw_data.items():
        for team, riders in race_data.items():
            for rider in riders:
                all_riders[rider]['races'].add(race_id)
    
    # Convert sets to lists for JSON serialization
    processed_riders = {}
    for rider, info in all_riders.items():
        processed_riders[rider] = {
            'team': info['team'],
            'races': list(info['races'])  # Convert set to list here
        }
    
    # Convert to final format
    return {
        'teams': sorted(list(all_teams)),
        'riders': processed_riders,  # Use the processed riders with lists instead of sets
        'races': list(raw_data.keys())
    }
