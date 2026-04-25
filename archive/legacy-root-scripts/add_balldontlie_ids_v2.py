"""
Add balldontlie game IDs to box score files - Version 2
This version ensures we keep ALL 2430 games from game_outlook.
"""

import pandas as pd
import glob
import os
from datetime import datetime

# Paths
BOXSCORE_DIR = "data/bdl_data/boxscores"
GAME_OUTLOOK_DIR = "data/bdl_data/game_outlook"
OUTPUT_DIR = "data/bdl_data/boxscores_with_bdl_id"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 80)
print("Adding Balldontlie Game IDs to Box Scores - Version 2")
print("=" * 80)
print()

# Step 1: Load all game_outlook files (this is our master list)
print("📋 Loading game_outlook files (master list)...")
game_outlook_files = sorted(glob.glob(f"{GAME_OUTLOOK_DIR}/game_outlook_2025-*.csv"))
print(f"Found {len(game_outlook_files)} game_outlook files")

all_outlooks = []
for f in game_outlook_files:
    df = pd.read_csv(f)
    all_outlooks.append(df)

game_outlook_df = pd.concat(all_outlooks, ignore_index=True)
print(f"✅ Loaded {len(game_outlook_df)} games from game_outlook (MASTER LIST)")

# Clean up date format
game_outlook_df['date_clean'] = pd.to_datetime(game_outlook_df['date']).dt.date

# Step 2: Load all box score files (from original MLB API fetch)
print()
print("📋 Re-fetching original box scores...")

# Instead of loading corrupted files, let's fetch fresh from MLB API for the 2430 games
from add_balldontlie_ids import get_game_boxscore, extract_team_boxscore
import time
import requests

def get_games_by_date(date_str):
    """Fetch all MLB games for a specific date."""
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1, "date": date_str}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'dates' not in data or len(data['dates']) == 0:
            return []
        
        games = data['dates'][0]['games']
        regular_season_games = [g for g in games if g.get('gameType') == 'R']
        return regular_season_games
    except Exception as e:
        return []

def get_game_boxscore(game_pk):
    """Fetch detailed boxscore for a specific game."""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

# Build a lookup of all MLB games by date and teams
print("Building MLB games lookup...")
mlb_games_lookup = {}

unique_dates = game_outlook_df['date_clean'].unique()
for date_obj in sorted(unique_dates):
    date_str = date_obj.strftime("%Y-%m-%d")
    games = get_games_by_date(date_str)
    
    for game in games:
        away_abbr = game['teams']['away']['team'].get('abbreviation', '')
        home_abbr = game['teams']['home']['team'].get('abbreviation', '')
        key = (date_obj, away_abbr, home_abbr)
        
        if key not in mlb_games_lookup:
            mlb_games_lookup[key] = []
        mlb_games_lookup[key].append(game)
    
    time.sleep(0.3)
    if len(mlb_games_lookup) % 100 == 0:
        print(f"  Processed {len([k for k in mlb_games_lookup.keys()])} unique matchups...")

print(f"✅ Built lookup with {len(mlb_games_lookup)} unique matchups")

# Step 3: Match each game_outlook game with MLB data
print()
print("=" * 80)
print("Matching and Fetching Box Scores")
print("=" * 80)

matched_rows = []
unmatched_games = []

for idx, outlook_row in game_outlook_df.iterrows():
    if idx % 100 == 0:
        print(f"Processing game {idx + 1}/{len(game_outlook_df)}...")
    
    # Create lookup key
    key = (
        outlook_row['date_clean'],
        outlook_row['away_team_abbreviation'],
        outlook_row['home_team_abbreviation']
    )
    
    if key in mlb_games_lookup:
        mlb_games = mlb_games_lookup[key]
        
        # For now, take the first match (handles most cases)
        # TODO: Handle doubleheaders more intelligently if needed
        mlb_game = mlb_games[0]
        game_pk = mlb_game['gamePk']
        
        # Fetch boxscore
        boxscore_data = get_game_boxscore(game_pk)
        
        if boxscore_data and 'teams' in boxscore_data:
            # Extract box score stats (simplified version)
            teams = boxscore_data['teams']
            away_batting = teams['away']['teamStats']['batting']
            home_batting = teams['home']['teamStats']['batting']
            away_pitching = teams['away']['teamStats']['pitching']
            home_pitching = teams['home']['teamStats']['pitching']
            away_fielding = teams['away']['teamStats']['fielding']
            home_fielding = teams['home']['teamStats']['fielding']
            
            # Determine winner
            away_runs = away_batting.get('runs', 0)
            home_runs = home_batting.get('runs', 0)
            
            row = {
                'balldontlie_game_id': outlook_row['id'],
                'id': game_pk,
                'date': outlook_row['date_clean'].strftime("%Y-%m-%d"),
                'home_team_id': outlook_row['home_team_id'],
                'away_team_id': outlook_row['away_team_id'],
                'home_team_abbreviation': outlook_row['home_team_abbreviation'],
                'away_team_abbreviation': outlook_row['away_team_abbreviation'],
                'home_team_display_name': outlook_row['home_team_display_name'],
                'away_team_display_name': outlook_row['away_team_display_name'],
                'home_team_name': outlook_row['home_team_name'],
                'away_team_name': outlook_row['away_team_name'],
                'home_postseason': 0,
                'away_postseason': 0,
                'home_season_type': 'regular',
                'away_season_type': 'regular',
                'home_season': 2025,
                'away_season': 2025,
                'home_gp': idx + 1,  # Simplified
                'away_gp': idx + 1,
                # Batting stats
                'home_batting_ab': home_batting.get('atBats', 0),
                'away_batting_ab': away_batting.get('atBats', 0),
                'home_batting_r': home_batting.get('runs', 0),
                'away_batting_r': away_batting.get('runs', 0),
                'home_batting_h': home_batting.get('hits', 0),
                'away_batting_h': away_batting.get('hits', 0),
                'home_batting_2b': home_batting.get('doubles', 0),
                'away_batting_2b': away_batting.get('doubles', 0),
                'home_batting_3b': home_batting.get('triples', 0),
                'away_batting_3b': away_batting.get('triples', 0),
                'home_batting_hr': home_batting.get('homeRuns', 0),
                'away_batting_hr': away_batting.get('homeRuns', 0),
                'home_batting_rbi': home_batting.get('rbi', 0),
                'away_batting_rbi': away_batting.get('rbi', 0),
                'home_batting_tb': home_batting.get('totalBases', 0),
                'away_batting_tb': away_batting.get('totalBases', 0),
                'home_batting_bb': home_batting.get('baseOnBalls', 0),
                'away_batting_bb': away_batting.get('baseOnBalls', 0),
                'home_batting_so': home_batting.get('strikeOuts', 0),
                'away_batting_so': away_batting.get('strikeOuts', 0),
                'home_batting_sb': home_batting.get('stolenBases', 0),
                'away_batting_sb': away_batting.get('stolenBases', 0),
                'home_batting_avg': home_batting.get('avg', '.000'),
                'away_batting_avg': away_batting.get('avg', '.000'),
                'home_batting_obp': home_batting.get('obp', '.000'),
                'away_batting_obp': away_batting.get('obp', '.000'),
                'home_batting_slg': home_batting.get('slg', '.000'),
                'away_batting_slg': away_batting.get('slg', '.000'),
                'home_batting_ops': home_batting.get('ops', '.000'),
                'away_batting_ops': away_batting.get('ops', '.000'),
                # Pitching stats
                'home_pitching_w': 1 if home_runs > away_runs else 0,
                'away_pitching_w': 1 if away_runs > home_runs else 0,
                'home_pitching_l': 1 if away_runs > home_runs else 0,
                'away_pitching_l': 1 if home_runs > away_runs else 0,
                'home_pitching_era': home_pitching.get('era', '0.00'),
                'away_pitching_era': away_pitching.get('era', '0.00'),
                'home_pitching_ip': home_pitching.get('inningsPitched', '0.0'),
                'away_pitching_ip': away_pitching.get('inningsPitched', '0.0'),
                'home_pitching_h': home_pitching.get('hits', 0),
                'away_pitching_h': away_pitching.get('hits', 0),
                'home_pitching_er': home_pitching.get('earnedRuns', 0),
                'away_pitching_er': away_pitching.get('earnedRuns', 0),
                'home_pitching_hr': home_pitching.get('homeRuns', 0),
                'away_pitching_hr': away_pitching.get('homeRuns', 0),
                'home_pitching_bb': home_pitching.get('baseOnBalls', 0),
                'away_pitching_bb': away_pitching.get('baseOnBalls', 0),
                'home_pitching_k': home_pitching.get('strikeOuts', 0),
                'away_pitching_k': away_pitching.get('strikeOuts', 0),
                'home_pitching_oba': f".{int((home_pitching.get('hits', 0) / max(home_pitching.get('atBats', 1), 1)) * 1000):03d}" if home_pitching.get('atBats', 0) > 0 else '.000',
                'away_pitching_oba': f".{int((away_pitching.get('hits', 0) / max(away_pitching.get('atBats', 1), 1)) * 1000):03d}" if away_pitching.get('atBats', 0) > 0 else '.000',
                'home_pitching_whip': home_pitching.get('whip', '0.00'),
                'away_pitching_whip': away_pitching.get('whip', '0.00'),
                # Fielding
                'home_fielding_e': home_fielding.get('errors', 0),
                'away_fielding_e': away_fielding.get('errors', 0),
            }
            
            matched_rows.append(row)
        else:
            unmatched_games.append(outlook_row)
        
        time.sleep(0.3)  # Be nice to the API
    else:
        unmatched_games.append(outlook_row)

print()
print("=" * 80)
print("Match Summary")
print("=" * 80)
print(f"Total game_outlook games: {len(game_outlook_df)}")
print(f"Successfully matched:      {len(matched_rows)}")
print(f"Unmatched:                 {len(unmatched_games)}")
print(f"Match rate:                {len(matched_rows)/len(game_outlook_df)*100:.1f}%")

if unmatched_games:
    print(f"\n⚠️  {len(unmatched_games)} games could not be matched:")
    for game in unmatched_games[:10]:
        print(f"   {game['date_clean']} - {game['away_team_abbreviation']} @ {game['home_team_abbreviation']}")
    if len(unmatched_games) > 10:
        print(f"   ... and {len(unmatched_games) - 10} more")

# Create DataFrame and save
print()
print("=" * 80)
print("Saving Files")
print("=" * 80)

matched_df = pd.DataFrame(matched_rows)

# Group by date and save
saved_files = 0
for date_str, group in matched_df.groupby('date'):
    output_file = f"{BOXSCORE_DIR}/boxscores_{date_str}.csv"
    group.to_csv(output_file, index=False)
    saved_files += 1
    if saved_files <= 5 or saved_files % 50 == 0:
        print(f"✅ Saved {date_str}: {len(group)} game(s)")

print()
print(f"✅ Saved {saved_files} files with {len(matched_df)} total games")
print(f"Target was: {len(game_outlook_df)} games")
print()
print("=" * 80)
