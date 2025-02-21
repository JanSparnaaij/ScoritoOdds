import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_omloop_startlist():
    url = "https://www.procyclingstats.com/race/omloop-het-nieuwsblad/2025/startlist/startlist"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page, status code: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    teams = []
    riders = []
    
    # Find all teams (inside <div class="ridersCont">)
    team_containers = soup.find_all("div", class_="ridersCont")
    
    for team in team_containers:
        # Extract team name
        team_name_tag = team.find("a", class_="team")
        if not team_name_tag:
            continue
        team_name = team_name_tag.text.strip()
        
        # Extract all riders inside <ul><li>
        rider_elements = team.find_all("li")
        
        for rider in rider_elements:
            rider_link = rider.find("a")  # Rider's name is inside <a> tag
            if rider_link:
                rider_name = rider_link.text.strip()
                riders.append(rider_name)
                teams.append(team_name)
    
    # Store in a DataFrame
    df = pd.DataFrame({"Rider": riders, "Team": teams})
    
    return df

if __name__ == "__main__":
    startlist_df = scrape_omloop_startlist()
    if startlist_df is not None:
        print(startlist_df)
        startlist_df.to_csv("omloop_2025_startlist.csv", index=False)
