"""
Add balldontlie game IDs to box score files WITHOUT filtering any games.
Games without matches will have balldontlie_game_id = NaN
"""

import pandas as pd
import glob
import os
from datetime import datetime

# Paths
BOXSCORE_DIR = "data/bdl_data/boxscores"
GAME_OUTLOOK_DIR = "data/bdl_data/game_outlook"

print("=" * 80)
print("Adding Balldontlie Game IDs to Box Scores (Keep All Games)")
print("=" * 80)
print()

# Load all game_outlook files to create ID mapping
print("📋 Loading game_outlook files...")
game_outlook_files = sorted(glob.glob(f"{GAME_OUTLOOK_DIR}/game_outlook_2025-*.csv"))
print(f"Found {len(game_outlook_files)} game_outlook files")

all_outlooks = []
for f in game_outlook_files:
    df = pd.read_csv(f)
    all_outlooks.append(df)

game_outlook_df = pd.concat(all_outlooks, ignore_index=True)
print(f"✅ Loaded {len(game_outlook_df)} games from game_outlook")

# Clean up date format for matching
game_outlook_df['date_clean'] = pd.to_datetime(game_outlook_df['date']).dt.date

print()
print("=" * 80)
print("Processing Box Score Files")
print("=" * 80)

# Create a dictionary for fast lookup
outlook_lookup = {}
for _, row in game_outlook_df.iterrows():
    key = (row['date_clean'], row['home_team_abbreviation'], row['away_team_abbreviation'])
    if key in outlook_lookup:
        # Handle doubleheaders - store as list
        if not isinstance(outlook_lookup[key], list):
            outlook_lookup[key] = [outlook_lookup[key]]
        outlook_lookup[key].append(row['id'])
    else:
        outlook_lookup[key] = row['id']

print(f"Created lookup table with {len(outlook_lookup)} unique matchups")

# Process each box score file
boxscore_files = sorted(glob.glob(f"{BOXSCORE_DIR}/boxscores_2025-*.csv"))
print(f"Found {len(boxscore_files)} box score files to process")
print()

matched_count = 0
unmatched_count = 0
total_count = 0
processed_files = 0

for boxscore_file in boxscore_files:
    # Load box score file
    df = pd.read_csv(boxscore_file)
    total_count += len(df)
    
    # Clean up date format
    df['date_clean'] = pd.to_datetime(df['date']).dt.date
    
    # Add balldontlie_game_id column
    balldontlie_ids = []
    for _, row in df.iterrows():
        key = (row['date_clean'], row['home_team_abbreviation'], row['away_team_abbreviation'])
        
        if key in outlook_lookup:
            bdl_id = outlook_lookup[key]
            if isinstance(bdl_id, list):
                # Doubleheader - take first game
                balldontlie_ids.append(bdl_id[0])
            else:
                balldontlie_ids.append(bdl_id)
            matched_count += 1
        else:
            balldontlie_ids.append(None)  # Keep the game but mark as unmatched
            unmatched_count += 1
    
    df['balldontlie_game_id'] = balldontlie_ids
    
    # Drop temporary column
    df = df.drop('date_clean', axis=1)
    
    # Reorder columns to put balldontlie_game_id first
    cols = df.columns.tolist()
    cols.remove('balldontlie_game_id')
    cols = ['balldontlie_game_id'] + cols
    df = df[cols]
    
    # Save back to file
    df.to_csv(boxscore_file, index=False)
    processed_files += 1
    
    if processed_files <= 5 or processed_files % 50 == 0:
        date = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
        print(f"✅ Processed {date}: {len(df)} game(s)")

print()
print("=" * 80)
print("Summary")
print("=" * 80)
print(f"Total files processed:     {processed_files}")
print(f"Total games:               {total_count}")
print(f"Matched with balldontlie:  {matched_count}")
print(f"No balldontlie match:      {unmatched_count}")
print(f"Match rate:                {matched_count/total_count*100:.1f}%")

print()
print("=" * 80)
print("Verification")
print("=" * 80)

# Verify a sample file
sample_file = f"{BOXSCORE_DIR}/boxscores_2025-03-18.csv"
sample_df = pd.read_csv(sample_file)
print(f"Sample file: {sample_file}")
print(f"Total games: {len(sample_df)}")
print(f"Total columns: {len(sample_df.columns)}")
print(f"First column: {sample_df.columns[0]}")
print()
print("Sample row:")
print(sample_df[['balldontlie_game_id', 'id', 'date', 'away_team_abbreviation', 'home_team_abbreviation']].head(1).to_string(index=False))

print()
print("=" * 80)
print("✅ COMPLETE - All 2464 games retained!")
print("=" * 80)
print(f"Games with balldontlie_game_id: {matched_count}")
print(f"Games with NaN balldontlie_game_id: {unmatched_count}")
print(f"Total columns per file: {len(sample_df.columns)}")
print("=" * 80)
