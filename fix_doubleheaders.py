"""
Fix doubleheader matching by adding game timestamps and re-matching with balldontlie IDs.
This handles the 307 unmatched games that are part of doubleheaders.
"""

import requests
import pandas as pd
import glob
from datetime import datetime
import time
import numpy as np

# Team abbreviation mappings
TEAM_ABB_MAPPING = {
    'AZ': 'ARI',   # Arizona Diamondbacks
    'CWS': 'CHW',  # Chicago White Sox
    'ATH': 'OAK'   # Oakland Athletics
}

def get_game_datetime(game_pk):
    """Fetch the game datetime from MLB API."""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Get game datetime from gameData section
        game_date = data.get('gameData', {}).get('datetime', {}).get('dateTime', None)
        return game_date
    except Exception as e:
        print(f"Error fetching datetime for game {game_pk}: {e}")
        return None

print("="*80)
print("STEP 1: Adding game timestamps to box scores")
print("="*80)

# Load all box scores
boxscore_files = sorted(glob.glob('data/bdl_data/boxscores/boxscores_2025-*.csv'))
print(f"Found {len(boxscore_files)} box score files")

updated_files = 0
games_with_timestamps = 0
games_without_timestamps = 0

for file_path in boxscore_files:
    df = pd.read_csv(file_path)
    
    # Check if datetime column already exists
    if 'datetime' in df.columns:
        print(f"✓ {file_path.split('/')[-1]} already has datetime column")
        continue
    
    print(f"Processing {file_path.split('/')[-1]}...")
    
    # Add datetime column
    datetimes = []
    for idx, row in df.iterrows():
        game_pk = row['id']
        game_datetime = get_game_datetime(game_pk)
        datetimes.append(game_datetime)
        
        if game_datetime:
            games_with_timestamps += 1
        else:
            games_without_timestamps += 1
        
        # Be respectful to API
        time.sleep(0.3)
    
    df['datetime'] = datetimes
    
    # Save updated file
    df.to_csv(file_path, index=False)
    updated_files += 1
    print(f"  ✅ Updated {len(df)} games")

print()
print(f"Updated {updated_files} files")
print(f"Games with timestamps: {games_with_timestamps}")
print(f"Games without timestamps: {games_without_timestamps}")

print()
print("="*80)
print("STEP 2: Re-matching with doubleheader support")
print("="*80)

# Load all box scores (now with datetime)
boxscores = pd.concat([pd.read_csv(f) for f in boxscore_files], ignore_index=True)
print(f"Loaded {len(boxscores)} box scores")

# Load all outlook data
outlook_files = sorted(glob.glob('data/bdl_data/game_outlook/game_outlook_2025-*.csv'))
outlook = pd.concat([pd.read_csv(f) for f in outlook_files], ignore_index=True)
print(f"Loaded {len(outlook)} outlook games")

# Map team abbreviations in outlook to match box scores
def map_team_abb(abb):
    return TEAM_ABB_MAPPING.get(abb, abb)

outlook['home_team_abb_mlb'] = outlook['home_team_abbreviation'].apply(map_team_abb)
outlook['away_team_abb_mlb'] = outlook['away_team_abbreviation'].apply(map_team_abb)

# Convert date columns
boxscores['date_clean'] = pd.to_datetime(boxscores['date']).dt.date
outlook['date_clean'] = pd.to_datetime(outlook['date']).dt.date

# Convert datetimes to comparable format
boxscores['datetime_parsed'] = pd.to_datetime(boxscores['datetime'], errors='coerce')
outlook['datetime_parsed'] = pd.to_datetime(outlook['date'])

print()
print("Matching games...")
print()

# Create a dictionary to store matches
matches = {}

# Group by date, home team, away team
for (date, home, away), group in outlook.groupby(['date_clean', 'home_team_abb_mlb', 'away_team_abb_mlb']):
    # Find matching box scores
    box_matches = boxscores[(boxscores['date_clean'] == date) & 
                            (boxscores['home_team_abbreviation'] == home) & 
                            (boxscores['away_team_abbreviation'] == away)]
    
    if len(box_matches) == 0:
        # No match found
        continue
    
    if len(group) == 1 and len(box_matches) == 1:
        # Single game - simple match
        matches[box_matches.iloc[0]['id']] = group.iloc[0]['id']
    
    elif len(group) >= 1 and len(box_matches) >= 1:
        # Doubleheader - match by closest datetime
        for _, outlook_game in group.iterrows():
            outlook_dt = outlook_game['datetime_parsed']
            
            if pd.isna(outlook_dt):
                continue
            
            # Find closest box score by time
            valid_box_matches = box_matches[box_matches['datetime_parsed'].notna()]
            
            if len(valid_box_matches) == 0:
                continue
            
            # Calculate time differences
            time_diffs = abs(valid_box_matches['datetime_parsed'] - outlook_dt)
            closest_idx = time_diffs.idxmin()
            closest_game = boxscores.loc[closest_idx]
            
            # Only match if within 6 hours (to avoid wrong matches)
            if time_diffs.loc[closest_idx].total_seconds() < 6 * 3600:
                matches[closest_game['id']] = outlook_game['id']

print(f"Matched {len(matches)} games")

# Add balldontlie_game_id to all box scores
boxscores['balldontlie_game_id'] = boxscores['id'].map(matches)

# Move balldontlie_game_id to first column
cols = ['balldontlie_game_id'] + [col for col in boxscores.columns if col != 'balldontlie_game_id']
boxscores = boxscores[cols]

print()
print("Results:")
print(f"  Total games: {len(boxscores)}")
print(f"  Matched: {boxscores['balldontlie_game_id'].notna().sum()} ({boxscores['balldontlie_game_id'].notna().sum()/len(boxscores)*100:.1f}%)")
print(f"  Unmatched: {boxscores['balldontlie_game_id'].isna().sum()} ({boxscores['balldontlie_game_id'].isna().sum()/len(boxscores)*100:.1f}%)")

print()
print("="*80)
print("STEP 3: Saving updated files")
print("="*80)

# Group by date and save
for date_str, group in boxscores.groupby('date'):
    file_path = f'data/bdl_data/boxscores/boxscores_{date_str}.csv'
    group.to_csv(file_path, index=False)

print(f"✅ Saved {boxscores['date'].nunique()} files")
print()
print("COMPLETE!")
print(f"Match rate improved from 87.5% to {boxscores['balldontlie_game_id'].notna().sum()/len(boxscores)*100:.1f}%")
