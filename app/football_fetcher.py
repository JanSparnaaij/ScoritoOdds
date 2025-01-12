from playwright.sync_api import sync_playwright
from flask import Flask, render_template, request, jsonify

# Flask app setup
app = Flask(__name__)

def fetch_all_matches(league_url):
    """
    Fetch match details and odds for a specific league.
    Args:
        league_url (str): URL of the league page on OddsPortal.

    Returns:
        list: List of dictionaries containing match details (team names, odds).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating to league: {league_url}")
        page.goto(league_url, timeout=60000)
        print("League page loaded successfully!")

        # Ensure the league page has loaded
        if "football" not in page.url:
            print(f"Failed to navigate to the league. Redirected to: {page.url}")
            browser.close()
            return None

        print("League page loaded successfully!")

        try:
            # Wait for the parent container of matches
            page.wait_for_selector('div[data-v-b8d70024] > div.eventRow', timeout=60000)

            # Locate all match containers
            match_containers = page.locator('div[data-v-b8d70024] > div.eventRow')
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

@app.route('/')
def index():
    """
    Render the homepage with dropdown options for leagues.
    """
    return render_template('index.html')

@app.route('/matches', methods=['POST'])
def get_matches():
    """
    Fetch matches based on the selected league.
    """
    country = request.form.get('country')
    league = request.form.get('league')
    league_url = f"https://www.oddsportal.com/football/{country}/{league}/"

    matches = fetch_all_matches(league_url)
    if matches:
        return jsonify(matches)
    else:
        return jsonify({"error": "Failed to fetch matches"}), 500

if __name__ == "__main__":
    app.run(debug=True)
