"""
Test script to fetch starting pitchers for the first game of the season.
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
BALLDONTLIE_API_KEY = os.getenv('BALLDONTLIE_API_KEY')

BASE_URL = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": BALLDONTLIE_API_KEY}

# Load the matchup data
csv_path = 'training-data/bdl-training-set/matchup_data.csv'
df = pd.read_csv(csv_path)

print("=" * 60)
print("TESTING FIRST GAME")
print("=" * 60)

# Get first game
first_game = df.iloc[0]
print(f"\nFirst game details:")
print(f"Date: {first_game['Date']}")
print(f"Home: {first_game['Home']}")
print(f"Away: {first_game['Away']}")
print(f"Fav Team: {first_game['Fav Team']}")
print(f"Dog Team: {first_game['Dog Team']}")
print(f"Fav Home?: {first_game['Fav Home?']}")

# Step 1: Fetch game_id
print("\n" + "=" * 60)
print("STEP 1: Fetching game_id from API")
print("=" * 60)

url = f"{BASE_URL}/games"
params = {
    "dates[]": first_game['Date'],
    "per_page": 50
}

print(f"Request URL: {url}")
print(f"Params: {params}")

response = requests.get(url, headers=HEADERS, params=params)
print(f"Response status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    games = data.get('data', [])
    print(f"Found {len(games)} games on {first_game['Date']}")
    
    # Look for matching game
    game_id = None
    for game in games:
        game_home = game.get('home_team', {}).get('abbreviation')
        game_away = game.get('away_team', {}).get('abbreviation')
        
        print(f"  Game: {game_away} @ {game_home} (ID: {game.get('id')})")
        
        if game_home == first_game['Home'] and game_away == first_game['Away']:
            game_id = game.get('id')
            print(f"\n✓ MATCH FOUND: Game ID = {game_id}")
            break
    
    if not game_id:
        print("\n✗ No matching game found!")
        print(f"Looking for: {first_game['Away']} @ {first_game['Home']}")
        exit(1)
else:
    print(f"Error: {response.text}")
    exit(1)

# Step 2: Fetch plate appearances
print("\n" + "=" * 60)
print("STEP 2: Fetching plate appearances")
print("=" * 60)

url = f"{BASE_URL}/plate_appearances"
params = {"game_id": game_id}

print(f"Request URL: {url}")
print(f"Params: {params}")

response = requests.get(url, headers=HEADERS, params=params)
print(f"Response status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    plate_appearances = data.get('data', [])
    print(f"Found {len(plate_appearances)} plate appearances")
    
    if len(plate_appearances) == 0:
        print("\n✗ No plate appearances found!")
        exit(1)
    
    # Convert to DataFrame
    df_pa = pd.DataFrame(plate_appearances)
    print(f"\nColumns in plate appearances: {df_pa.columns.tolist()}")
    
    # Look at first few plate appearances
    print(f"\nFirst 5 plate appearances:")
    for i, pa in enumerate(plate_appearances[:5]):
        print(f"\n  PA {i+1}:")
        print(f"    Inning: {pa.get('inning')}")
        print(f"    Half: {pa.get('half_inning')}")
        print(f"    Pitcher ID: {pa.get('pitcher_id')}")
        pitcher = pa.get('pitcher', {})
        if pitcher:
            print(f"    Pitcher Name: {pitcher.get('first_name')} {pitcher.get('last_name')}")
    
    # Step 3: Find starters
    print("\n" + "=" * 60)
    print("STEP 3: Identifying starters")
    print("=" * 60)
    
    # Sort by inning and half
    df_pa['half_order'] = df_pa['half_inning'].apply(lambda x: 0 if x == 'top' else 1)
    df_pa = df_pa.sort_values(['inning', 'half_order'])
    
    # Find home starter (first top-1 appearance - pitching TO away batters)
    home_starter_id = None
    home_starter_name = None
    top_1 = df_pa[(df_pa['inning'] == 1) & (df_pa['half_inning'] == 'top')]
    if not top_1.empty:
        first_pa = top_1.iloc[0]
        home_starter_id =first_pa.get('pitcher_id')
        pitcher = first_pa.get('pitcher', {})
        home_starter_name = f"{pitcher.get('first_name', '')} {pitcher.get('last_name', '')}".strip()
        
        # If name is empty, fetch from player endpoint
        if not home_starter_name and home_starter_id:
            print(f"\nFetching home pitcher name from player endpoint...")
            player_url = f"{BASE_URL}/players/{home_starter_id}"
            player_response = requests.get(player_url, headers=HEADERS)
            if player_response.status_code == 200:
                player_json = player_response.json()
                player_data = player_json.get('data', {})
                home_starter_name = f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip()
                print(f"  Response: {player_data.get('full_name', 'No name found')}")
            else:
                print(f"  Error fetching player: {player_response.status_code}")
        
        print(f"\nHome starter (first top-1 PA - pitching TO away batters):")
        print(f"  ID: {home_starter_id}")
        print(f"  Name: {home_starter_name}")
    else:
        print("\n✗ No top-1 plate appearances found!")
    
    # Find away starter (first bottom-1 appearance - pitching TO home batters)
    away_starter_id = None
    away_starter_name = None
    bottom_1 = df_pa[(df_pa['inning'] == 1) & (df_pa['half_inning'] == 'bottom')]
    if not bottom_1.empty:
        first_pa = bottom_1.iloc[0]
        away_starter_id = first_pa.get('pitcher_id')
        pitcher = first_pa.get('pitcher', {})
        away_starter_name = f"{pitcher.get('first_name', '')} {pitcher.get('last_name', '')}".strip()
        
        # If name is empty, fetch from player endpoint
        if not away_starter_name and away_starter_id:
            print(f"\nFetching away pitcher name from player endpoint...")
            player_url = f"{BASE_URL}/players/{away_starter_id}"
            player_response = requests.get(player_url, headers=HEADERS)
            if player_response.status_code == 200:
                player_json = player_response.json()
                player_data = player_json.get('data', {})
                away_starter_name = f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip()
                print(f"  Response: {player_data.get('full_name', 'No name found')}")
            else:
                print(f"  Error fetching player: {player_response.status_code}")
        
        print(f"\nAway starter (first bottom-1 PA - pitching TO home batters):")
        print(f"  ID: {away_starter_id}")
        print(f"  Name: {away_starter_name}")
    else:
        print("\n✗ No bottom-1 plate appearances found!")
    
    # Step 4: Map to Favorite/Underdog
    print("\n" + "=" * 60)
    print("STEP 4: Mapping to Favorite/Underdog")
    print("=" * 60)
    
    print(f"\nAway team: {first_game['Away']} - Starter: {away_starter_name}")
    print(f"Home team: {first_game['Home']} - Starter: {home_starter_name}")
    print(f"Fav Home?: {first_game['Fav Home?']}")
    
    if first_game['Fav Home?'] == 1:
        fav_starter = home_starter_name
        dog_starter = away_starter_name
        print(f"\nFavorite (Home): {first_game['Fav Team']} - Starter: {fav_starter}")
        print(f"Underdog (Away): {first_game['Dog Team']} - Starter: {dog_starter}")
    else:
        fav_starter = away_starter_name
        dog_starter = home_starter_name
        print(f"\nFavorite (Away): {first_game['Fav Team']} - Starter: {fav_starter}")
        print(f"Underdog (Home): {first_game['Dog Team']} - Starter: {dog_starter}")
    
    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    
else:
    print(f"Error: {response.text}")
    exit(1)
