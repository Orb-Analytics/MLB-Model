"""
Populate a single game's data from balldontlie API into the training CSV.
Game: 2025-08-16, SEA @ NYM
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BALLDONTLIE_API_KEY = os.getenv('BALLDONTLIE_API_KEY')

BASE_URL = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": BALLDONTLIE_API_KEY}

# Game details
GAME_DATE = "2025-08-16"
AWAY_TEAM = "SEA"
HOME_TEAM = "NYM"

print("=" * 80)
print(f"POPULATING DATA FOR: {GAME_DATE} - {AWAY_TEAM} @ {HOME_TEAM}")
print("=" * 80)

# Load CSV
csv_path = 'training-data/bdl-training-set/matchup_data.csv'
df = pd.read_csv(csv_path)

# Find the game row
game_row = df[(df['Date'] == GAME_DATE) & (df['Away'] == AWAY_TEAM) & (df['Home'] == HOME_TEAM)]

if game_row.empty:
    print(f"\n✗ Game not found in CSV")
    exit(1)

game_idx = game_row.index[0]
print(f"\n✓ Found game at row {game_idx}")
print(f"  Fav Team: {game_row.iloc[0]['Fav Team']}")
print(f"  Dog Team: {game_row.iloc[0]['Dog Team']}")
print(f"  Fav Home?: {game_row.iloc[0]['Fav Home?']}")

# ============================================================================
# STEP 1: GET STARTING PITCHERS
# ============================================================================
print("\n" + "=" * 80)
print("STEP 1: GETTING STARTING PITCHERS")
print("=" * 80)

# Get game_id
url = f"{BASE_URL}/games"
params = {"dates[]": GAME_DATE, "per_page": 50}
response = requests.get(url, headers=HEADERS, params=params)
games = response.json().get('data', [])

game_id = None
for game in games:
    if game.get('home_team', {}).get('abbreviation') == HOME_TEAM and \
       game.get('away_team', {}).get('abbreviation') == AWAY_TEAM:
        game_id = game.get('id')
        break

if not game_id:
    print("✗ Could not find game_id")
    exit(1)

print(f"✓ Game ID: {game_id}")

# Get plate appearances
url = f"{BASE_URL}/plate_appearances"
params = {"game_id": game_id}
response = requests.get(url, headers=HEADERS, params=params)
plate_appearances = response.json().get('data', [])

df_pa = pd.DataFrame(plate_appearances)
df_pa['half_order'] = df_pa['half_inning'].apply(lambda x: 0 if x == 'top' else 1)
df_pa = df_pa.sort_values(['inning', 'half_order'])

# Home starter (top-1)
top_1 = df_pa[(df_pa['inning'] == 1) & (df_pa['half_inning'] == 'top')]
home_starter_id = top_1.iloc[0].get('pitcher_id') if not top_1.empty else None

# Away starter (bottom-1)
bottom_1 = df_pa[(df_pa['inning'] == 1) & (df_pa['half_inning'] == 'bottom')]
away_starter_id = bottom_1.iloc[0].get('pitcher_id') if not bottom_1.empty else None

# Get pitcher names
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

# Map to Favorite/Underdog
fav_home = game_row.iloc[0]['Fav Home?']
if fav_home == 1:  # Favorite is home
    fav_starter_name = home_starter_name
    dog_starter_name = away_starter_name
    fav_starter_id = home_starter_id
    dog_starter_id = away_starter_id
else:  # Favorite is away
    fav_starter_name = away_starter_name
    dog_starter_name = home_starter_name
    fav_starter_id = away_starter_id
    dog_starter_id = home_starter_id

print(f"\n✓ Favorite Starter: {fav_starter_name}")
print(f"✓ Underdog Starter: {dog_starter_name}")

# Update CSV with pitcher names
df.at[game_idx, 'Favorite Starting Pitcher Name'] = fav_starter_name
df.at[game_idx, 'Underdog Starting Pitcher Name'] = dog_starter_name

# ============================================================================
# STEP 2: GET PITCHER SEASON STATS
# ============================================================================
print("\n" + "=" * 80)
print("STEP 2: GETTING PITCHER SEASON STATS")
print("=" * 80)

def get_pitcher_stats(player_id, player_name):
    """Get pitcher season stats."""
    print(f"\n  Fetching stats for {player_name} (ID: {player_id})...")
    
    url = f"{BASE_URL}/season_stats"
    params = {"player_ids[]": player_id, "season": 2025}
    
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"    ✗ Error: {response.text}")
        return None
    
    data = response.json().get('data', [])
    pitching_stats = [s for s in data if s.get('stat_type') == 'pitching']
    
    if not pitching_stats:
        print(f"    ✗ No pitching stats found")
        return None
    
    stats = pitching_stats[0]
    print(f"    ✓ ERA: {stats.get('era', 'N/A')}, WHIP: {stats.get('whip', 'N/A')}, IP: {stats.get('innings_pitched', 'N/A')}")
    
    return stats

fav_stats = get_pitcher_stats(fav_starter_id, fav_starter_name)
dog_stats = get_pitcher_stats(dog_starter_id, dog_starter_name)

# Update CSV with pitcher stats
if fav_stats:
    df.at[game_idx, 'Favorite Starting Pitcher Earned Run Average'] = fav_stats.get('era')
    df.at[game_idx, 'Favorite Starting Pitcher Walks and Hits per Inning Pitched'] = fav_stats.get('whip')
    df.at[game_idx, 'Favorite Starting Pitcher Innings Pitched'] = fav_stats.get('innings_pitched')
    df.at[game_idx, 'Favorite Starting Pitcher Strikeouts'] = fav_stats.get('strikeouts')
    df.at[game_idx, 'Favorite Starting Pitcher At Bats Faced'] = fav_stats.get('batters_faced')
    
    # Calculate derived stats
    ip = fav_stats.get('innings_pitched', 0)
    ab = fav_stats.get('batters_faced', 0)
    k = fav_stats.get('strikeouts', 0)
    if ip and ip > 0:
        df.at[game_idx, 'Favorite Starting Pitcher At Bats Faced per Inning'] = round(ab / ip, 3) if ab else None
    if ab and ab > 0:
        df.at[game_idx, 'Favorite Starting Pitcher Strikeouts per At Bat'] = round(k / ab, 3) if k else None

if dog_stats:
    df.at[game_idx, 'Underdog Starting Pitcher Earned Run Average'] = dog_stats.get('era')
    df.at[game_idx, 'Underdog Starting Pitcher Walks and Hits per Inning Pitched'] = dog_stats.get('whip')
    df.at[game_idx, 'Underdog Starting Pitcher Innings Pitched'] = dog_stats.get('innings_pitched')
    df.at[game_idx, 'Underdog Starting Pitcher Strikeouts'] = dog_stats.get('strikeouts')
    df.at[game_idx, 'Underdog Starting Pitcher At Bats Faced'] = dog_stats.get('batters_faced')
    
    # Calculate derived stats
    ip = dog_stats.get('innings_pitched', 0)
    ab = dog_stats.get('batters_faced', 0)
    k = dog_stats.get('strikeouts', 0)
    if ip and ip > 0:
        df.at[game_idx, 'Underdog Starting Pitcher At Bats Faced per Inning'] = round(ab / ip, 3) if ab else None
    if ab and ab > 0:
        df.at[game_idx, 'Underdog Starting Pitcher Strikeouts per At Bat'] = round(k / ab, 3) if k else None

# ============================================================================
# STEP 3: GET TEAM STATS
# ============================================================================
print("\n" + "=" * 80)
print("STEP 3: GETTING TEAM SEASON STATS")
print("=" * 80)

def get_team_id(team_abbr):
    """Get team ID."""
    url = f"{BASE_URL}/games"
    params = {"dates[]": GAME_DATE, "per_page": 50}
    response = requests.get(url, headers=HEADERS, params=params)
    games = response.json().get('data', [])
    
    for game in games:
        if game.get('home_team', {}).get('abbreviation') == team_abbr:
            return game.get('home_team', {}).get('id')
        elif game.get('away_team', {}).get('abbreviation') == team_abbr:
            return game.get('away_team', {}).get('id')
    return None

def get_team_stats(team_abbr):
    """Get team season stats."""
    print(f"\n  Fetching stats for {team_abbr}...")
    
    team_id = get_team_id(team_abbr)
    if not team_id:
        print(f"    ✗ Could not find team_id")
        return None
    
    url = f"{BASE_URL}/teams/season_stats"
    params = {"team_ids[]": team_id, "season": 2025}
    
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"    ✗ Error: {response.text}")
        return None
    
    data = response.json().get('data', [])
    if not data:
        print(f"    ✗ No team stats found")
        return None
    
    stats = data[0]
    print(f"    ✓ Pitching ERA: {stats.get('pitching_era', 'N/A')}, Batting AVG: {stats.get('batting_avg', 'N/A')}")
    
    return stats

fav_team = game_row.iloc[0]['Fav Team']
dog_team = game_row.iloc[0]['Dog Team']

fav_team_stats = get_team_stats(fav_team)
dog_team_stats = get_team_stats(dog_team)

# Update CSV with team pitching stats
if fav_team_stats:
    df.at[game_idx, 'Favorite Team Pitching Earned Run Average'] = fav_team_stats.get('pitching_era')
    df.at[game_idx, 'Favorite Team Pitching Walks and Hits per Inning Pitched'] = fav_team_stats.get('pitching_whip')
    df.at[game_idx, 'Favorite Team Pitching Innings Pitched'] = fav_team_stats.get('pitching_ip')
    df.at[game_idx, 'Favorite Team Pitching Strikeouts'] = fav_team_stats.get('pitching_k')
    df.at[game_idx, 'Favorite Team Pitching Walks'] = fav_team_stats.get('pitching_bb')
    df.at[game_idx, 'Favorite Team Pitching Hits Allowed'] = fav_team_stats.get('pitching_h')
    df.at[game_idx, 'Favorite Team Pitching Home Runs Allowed'] = fav_team_stats.get('pitching_hr')
    df.at[game_idx, 'Favorite Team Pitching Earned Runs'] = fav_team_stats.get('pitching_er')
    
    # Batting stats
    df.at[game_idx, 'Favorite Team Batting Average'] = fav_team_stats.get('batting_avg')
    df.at[game_idx, 'Favorite Team On Base Percentage'] = fav_team_stats.get('batting_obp')
    df.at[game_idx, 'Favorite Team Slugging Percentage'] = fav_team_stats.get('batting_slg')
    df.at[game_idx, 'Favorite Team On Base Plus Slugging'] = fav_team_stats.get('batting_ops')
    df.at[game_idx, 'Favorite Team Runs'] = fav_team_stats.get('batting_r')
    df.at[game_idx, 'Favorite Team Hits'] = fav_team_stats.get('batting_h')
    df.at[game_idx, 'Favorite Team Home Runs'] = fav_team_stats.get('batting_hr')
    df.at[game_idx, 'Favorite Team Runs Batted In'] = fav_team_stats.get('batting_rbi')
    df.at[game_idx, 'Favorite Team Stolen Bases'] = fav_team_stats.get('batting_sb')

if dog_team_stats:
    df.at[game_idx, 'Underdog Team Pitching Earned Run Average'] = dog_team_stats.get('pitching_era')
    df.at[game_idx, 'Underdog Team Pitching Walks and Hits per Inning Pitched'] = dog_team_stats.get('pitching_whip')
    df.at[game_idx, 'Underdog Team Pitching Innings Pitched'] = dog_team_stats.get('pitching_ip')
    df.at[game_idx, 'Underdog Team Pitching Strikeouts'] = dog_team_stats.get('pitching_k')
    df.at[game_idx, 'Underdog Team Pitching Walks'] = dog_team_stats.get('pitching_bb')
    df.at[game_idx, 'Underdog Team Pitching Hits Allowed'] = dog_team_stats.get('pitching_h')
    df.at[game_idx, 'Underdog Team Pitching Home Runs Allowed'] = dog_team_stats.get('pitching_hr')
    df.at[game_idx, 'Underdog Team Pitching Earned Runs'] = dog_team_stats.get('pitching_er')
    
    # Batting stats
    df.at[game_idx, 'Underdog Team Batting Average'] = dog_team_stats.get('batting_avg')
    df.at[game_idx, 'Underdog Team On Base Percentage'] = dog_team_stats.get('batting_obp')
    df.at[game_idx, 'Underdog Team Slugging Percentage'] = dog_team_stats.get('batting_slg')
    df.at[game_idx, 'Underdog Team On Base Plus Slugging'] = dog_team_stats.get('batting_ops')
    df.at[game_idx, 'Underdog Team Runs'] = dog_team_stats.get('batting_r')
    df.at[game_idx, 'Underdog Team Hits'] = dog_team_stats.get('batting_h')
    df.at[game_idx, 'Underdog Team Home Runs'] = dog_team_stats.get('batting_hr')
    df.at[game_idx, 'Underdog Team Runs Batted In'] = dog_team_stats.get('batting_rbi')
    df.at[game_idx, 'Underdog Team Stolen Bases'] = dog_team_stats.get('batting_sb')

# ============================================================================
# SAVE CSV
# ============================================================================
print("\n" + "=" * 80)
print("SAVING UPDATED CSV")
print("=" * 80)

df.to_csv(csv_path, index=False)
print(f"\n✓ Saved to {csv_path}")

# Show what was populated
print("\n" + "=" * 80)
print("SUMMARY OF POPULATED DATA")
print("=" * 80)

populated_cols = []
for col in df.columns:
    val = df.at[game_idx, col]
    if pd.notna(val) and val != '' and col not in ['Date', 'Fav Team', 'Dog Team', 'Away', 'Home', 'Fav Home?', 'Fav Score', 'Dog Score', 'Fav/Dog +/-', 'Fav Cover?', 'Fav Win?', 'Away Score', 'Home Score', 'Home/Away +/-']:
        populated_cols.append(col)

print(f"\n✓ Populated {len(populated_cols)} columns:")
for col in populated_cols:
    print(f"  - {col}: {df.at[game_idx, col]}")

print("\n✓ COMPLETE!")
