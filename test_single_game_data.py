"""
Test fetching ALL data for a single game: 2025-08-16, NYM @ SEA
Retrieve data step by step to see what's available from balldontlie.
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
BALLDONTLIE_API_KEY = os.getenv('BALLDONTLIE_API_KEY')

BASE_URL = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": BALLDONTLIE_API_KEY}

# Game details
GAME_DATE = "2025-08-16"
AWAY_TEAM = "SEA"  # Seattle Mariners
HOME_TEAM = "NYM"  # New York Mets
DATA_CUTOFF_DATE = "2025-08-15"  # Get stats up to day before game

print("=" * 80)
print(f"TESTING DATA AVAILABILITY FOR: {GAME_DATE} - {AWAY_TEAM} @ {HOME_TEAM}")
print(f"Data cutoff: {DATA_CUTOFF_DATE} (stats up to day before game)")
print("=" * 80)

# ============================================================================
# STEP 1: GET GAME_ID AND STARTING PITCHERS
# ============================================================================
print("\n" + "=" * 80)
print("STEP 1: GET GAME_ID AND STARTING PITCHER NAMES")
print("=" * 80)

# Fetch game_id
print(f"\n1.1 Fetching game_id for {GAME_DATE}...")
url = f"{BASE_URL}/games"
params = {"dates[]": GAME_DATE, "per_page": 50}
response = requests.get(url, headers=HEADERS, params=params)

if response.status_code != 200:
    print(f"ERROR: {response.text}")
    exit(1)

games = response.json().get('data', [])
game_id = None
for game in games:
    if game.get('home_team', {}).get('abbreviation') == HOME_TEAM and \
       game.get('away_team', {}).get('abbreviation') == AWAY_TEAM:
        game_id = game.get('id')
        print(f"✓ Found game_id: {game_id}")
        break

if not game_id:
    print(f"✗ Could not find game")
    exit(1)

# Fetch plate appearances to get starting pitchers
print(f"\n1.2 Fetching plate appearances to identify starters...")
url = f"{BASE_URL}/plate_appearances"
params = {"game_id": game_id}
response = requests.get(url, headers=HEADERS, params=params)

if response.status_code != 200:
    print(f"ERROR: {response.text}")
    exit(1)

plate_appearances = response.json().get('data', [])
df_pa = pd.DataFrame(plate_appearances)

# Sort and find starters
df_pa['half_order'] = df_pa['half_inning'].apply(lambda x: 0 if x == 'top' else 1)
df_pa = df_pa.sort_values(['inning', 'half_order'])

# Home starter (top-1)
top_1 = df_pa[(df_pa['inning'] == 1) & (df_pa['half_inning'] == 'top')]
home_starter_id = top_1.iloc[0].get('pitcher_id') if not top_1.empty else None

# Away starter (bottom-1)
bottom_1 = df_pa[(df_pa['inning'] == 1) & (df_pa['half_inning'] == 'bottom')]
away_starter_id = bottom_1.iloc[0].get('pitcher_id') if not bottom_1.empty else None

# Fetch pitcher names
print(f"\n1.3 Fetching pitcher names from API...")
def get_player_name(player_id):
    url = f"{BASE_URL}/players/{player_id}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        player = resp.json().get('data', {})
        return f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
    return None

away_starter_name = get_player_name(away_starter_id) if away_starter_id else None
home_starter_name = get_player_name(home_starter_id) if home_starter_id else None

print(f"\n✓ Away Starter ({AWAY_TEAM}): {away_starter_name} (ID: {away_starter_id})")
print(f"✓ Home Starter ({HOME_TEAM}): {home_starter_name} (ID: {home_starter_id})")

# ============================================================================
# STEP 2: GET STARTING PITCHER SEASON STATS (up to 2025-08-15)
# ============================================================================
print("\n" + "=" * 80)
print("STEP 2: GET STARTING PITCHER SEASON STATS (up to cutoff date)")
print("=" * 80)

def get_pitcher_season_stats(player_id, player_name, team_abbr, cutoff_date):
    """Get pitcher's season stats up to cutoff date."""
    print(f"\n2.{player_name} ({team_abbr}) - Player ID: {player_id}")
    
    # Fetch season stats from season_stats endpoint
    url = f"{BASE_URL}/season_stats"
    params = {
        "player_ids[]": player_id,
        "season": 2025,
        "per_page": 100
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"  ✗ Error fetching season stats: {response.text}")
        return None
    
    data = response.json().get('data', [])
    
    if not data:
        print(f"  ✗ No season stats found")
        return None
    
    # Filter pitching stats
    pitching_stats = [s for s in data if s.get('stat_type') == 'pitching']
    
    if not pitching_stats:
        print(f"  ✗ No pitching stats found")
        return None
    
    stats = pitching_stats[0]
    
    print(f"  ✓ Found season stats:")
    print(f"    ERA: {stats.get('era', 'N/A')}")
    print(f"    WHIP: {stats.get('whip', 'N/A')}")
    print(f"    IP: {stats.get('innings_pitched', 'N/A')}")
    print(f"    K: {stats.get('strikeouts', 'N/A')}")
    print(f"    BB: {stats.get('walks', 'N/A')}")
    print(f"    H: {stats.get('hits_allowed', 'N/A')}")
    print(f"    ER: {stats.get('earned_runs', 'N/A')}")
    print(f"    Games: {stats.get('games_played', 'N/A')}")
    print(f"    Wins: {stats.get('wins', 'N/A')}")
    print(f"    Losses: {stats.get('losses', 'N/A')}")
    
    return stats

away_starter_stats = get_pitcher_season_stats(away_starter_id, away_starter_name, AWAY_TEAM, DATA_CUTOFF_DATE)
home_starter_stats = get_pitcher_season_stats(home_starter_id, home_starter_name, HOME_TEAM, DATA_CUTOFF_DATE)

# ============================================================================
# STEP 3: GET TEAM PITCHING STATS (up to 2025-08-15)
# ============================================================================
print("\n" + "=" * 80)
print("STEP 3: GET TEAM PITCHING STATS (season aggregate up to cutoff)")
print("=" * 80)

def get_team_season_stats(team_abbr):
    """Get team's season stats."""
    print(f"\n3. {team_abbr} Team Stats")
    
    # First get team_id
    url = f"{BASE_URL}/games"
    params = {"dates[]": GAME_DATE, "per_page": 50}
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"  ✗ Error fetching games: {response.text}")
        return None
    
    games = response.json().get('data', [])
    team_id = None
    for game in games:
        if game.get('home_team', {}).get('abbreviation') == team_abbr:
            team_id = game.get('home_team', {}).get('id')
            break
        elif game.get('away_team', {}).get('abbreviation') == team_abbr:
            team_id = game.get('away_team', {}).get('id')
            break
    
    if not team_id:
        print(f"  ✗ Could not find team_id")
        return None
    
    print(f"  Team ID: {team_id}")
    
    # Fetch team season stats
    url = f"{BASE_URL}/teams/season_stats"
    params = {
        "team_ids[]": team_id,
        "season": 2025
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"  ✗ Error fetching team stats: {response.text}")
        return None
    
    data = response.json().get('data', [])
    
    if not data:
        print(f"  ✗ No team stats found")
        return None
    
    stats = data[0]
    
    print(f"\n  ✓ PITCHING STATS:")
    print(f"    Team ERA: {stats.get('era', 'N/A')}")
    print(f"    Team WHIP: {stats.get('whip', 'N/A')}")
    print(f"    IP: {stats.get('innings_pitched', 'N/A')}")
    print(f"    K: {stats.get('strikeouts', 'N/A')}")
    print(f"    BB: {stats.get('walks', 'N/A')}")
    print(f"    H Allowed: {stats.get('hits_allowed', 'N/A')}")
    print(f"    Runs Allowed: {stats.get('runs_allowed', 'N/A')}")
    print(f"    ER: {stats.get('earned_runs', 'N/A')}")
    print(f"    HR Allowed: {stats.get('home_runs_allowed', 'N/A')}")
    print(f"    Saves: {stats.get('saves', 'N/A')}")
    print(f"    Blown Saves: {stats.get('blown_saves', 'N/A')}")
    
    print(f"\n  ✓ BATTING STATS:")
    print(f"    Team BA: {stats.get('batting_average', 'N/A')}")
    print(f"    OBP: {stats.get('on_base_percentage', 'N/A')}")
    print(f"    SLG: {stats.get('slugging_percentage', 'N/A')}")
    print(f"    OPS: {stats.get('on_base_plus_slugging', 'N/A')}")
    print(f"    Runs: {stats.get('runs', 'N/A')}")
    print(f"    Hits: {stats.get('hits', 'N/A')}")
    print(f"    HR: {stats.get('home_runs', 'N/A')}")
    print(f"    RBI: {stats.get('runs_batted_in', 'N/A')}")
    print(f"    SB: {stats.get('stolen_bases', 'N/A')}")
    
    return stats

away_team_stats = get_team_season_stats(AWAY_TEAM)
home_team_stats = get_team_season_stats(HOME_TEAM)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY: DATA AVAILABILITY CHECK")
print("=" * 80)

print(f"\n✓ Starting Pitchers: AVAILABLE")
print(f"  - {AWAY_TEAM}: {away_starter_name}")
print(f"  - {HOME_TEAM}: {home_starter_name}")

print(f"\n✓ Pitcher Season Stats: {'AVAILABLE' if away_starter_stats and home_starter_stats else 'PARTIAL/MISSING'}")
print(f"  - Stats are SEASON TOTALS (not filtered by date)")
print(f"  - NOTE: API may not filter by cutoff date automatically")

print(f"\n✓ Team Stats: {'AVAILABLE' if away_team_stats and home_team_stats else 'PARTIAL/MISSING'}")
print(f"  - Stats are SEASON TOTALS (not filtered by date)")
print(f"  - NOTE: API may not filter by cutoff date automatically")

print("\n" + "=" * 80)
print("LIMITATIONS DISCOVERED:")
print("=" * 80)
print("1. Season stats endpoints return FULL SEASON totals")
print("2. No built-in date filtering for 'stats up to X date'")
print("3. To get stats 'up to 2025-08-15', we need to:")
print("   - Fetch game-by-game stats for each pitcher/team")
print("   - Aggregate only games before cutoff date")
print("   - This requires many more API calls")
print("\nNext step: Test game-by-game stats aggregation...")
