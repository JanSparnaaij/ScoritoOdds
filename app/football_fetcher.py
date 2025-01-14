from playwright.async_api import async_playwright

async def fetch_all_matches_async(league_url):
    """
    Asynchronously fetch match details and odds for a specific league.

    Args:
        league_url (str): URL of the league page on OddsPortal.

    Returns:
        list: List of dictionaries containing match details (team names, odds).
    """
    async with async_playwright() as p:
        browser = None
        try:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            print(f"Navigating to league: {league_url}")
            await page.goto(league_url, timeout=20000)
            print("League page loaded successfully!")

            # Validate that the correct page is loaded
            if "football" not in page.url:
                print(f"Failed to navigate to the league. Redirected to: {page.url}")
                return None

            # Wait for the parent container of matches
            await page.wait_for_selector('div[data-v-b8d70024] > div.eventRow', timeout=20000)

            # Locate all match containers
            match_containers = page.locator('div[data-v-b8d70024] > div.eventRow')
            match_count = await match_containers.count()
            print(f"Found {match_count} match containers.")

            all_matches = []
            processed_ids = set()  # To track unique match rows

            for i in range(match_count):
                try:
                    # Scope to the current match container
                    container = match_containers.nth(i)
                    row_id = await container.get_attribute("id")

                    # Skip duplicates
                    if row_id in processed_ids:
                        print(f"Skipping duplicate row with ID {row_id}")
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
                    print(f"Match {row_id}: Home {home_odd}, Draw {draw_odd}, Away {away_odd}")

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
                    print(f"Error processing match {i + 1}: {e}")
                    continue

            return all_matches

        except Exception as e:
            print(f"Error fetching matches: {e}")
            return None

        finally:
            # Ensure the browser is closed
            if browser and browser.is_connected():
                await browser.close()
