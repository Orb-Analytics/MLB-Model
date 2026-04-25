"""
Add balldontlie game IDs to box score files by matching with game_outlook data.
This creates updated box score files with a new 'balldontlie_game_id' column.
"""

import pandas as pd
import glob
import os
from datetime import datetime

# Paths
BOXSCORE_DIR = "data/bdl_data/boxscores"
GAME_OUTLOOK_DIR = "data/bdl_data/game_outlook"

print("=" * 80)
print("Adding Balldontlie Game IDs to Box Scores")
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

# Load all box score files
print()
print("📋 Loading box score files...")
boxscore_files = sorted(glob.glob(f"{BOXSCORE_DIR}/boxscores_2025-*.csv"))
print(f"Found {len(boxscore_files)} box score files")

all_boxscores = []
for f in boxscore_files:
    df = pd.read_csv(f)
    all_boxscores.append(df)

boxscore_df = pd.concat(all_boxscores, ignore_index=True)
print(f"✅ Loaded {len(boxscore_df)} games from box scores")

# Clean up date format for matching
boxscore_df['date_clean'] = pd.to_datetime(boxscore_df['date']).dt.date

print()
print("=" * 80)
print("Matching Games")
print("=" * 80)

# Match on date, home team abbreviation, and away team abbreviation
matched_count = 0
unmatched_count = 0
duplicate_matches = 0

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

# Add balldontlie_game_id column
balldontlie_ids = []
for _, row in boxscore_df.iterrows():
    key = (row['date_clean'], row['home_team_abbreviation'], row['away_team_abbreviation'])
    
    if key in outlook_lookup:
        bdl_id = outlook_lookup[key]
        if isinstance(bdl_id, list):
            # Doubleheader - for now, take first game
            # In production, you'd need more logic to match correctly
            balldontlie_ids.append(bdl_id[0])
            duplicate_matches += 1
            print(f"⚠️  Doubleheader detected: {row['date']} {row['away_team_abbreviation']} @ {row['home_team_abbreviation']}")
        else:
            balldontlie_ids.append(bdl_id)
            matched_count += 1
    else:
        balldontlie_ids.append(None)
        unmatched_count += 1
        print(f"❌ No match: {row['date']} {row['away_team_abbreviation']} @ {row['home_team_abbreviation']} (MLB ID: {row['id']})")

boxscore_df['balldontlie_game_id'] = balldontlie_ids

print()
print("=" * 80)
print("Match Summary")
print("=" * 80)
print(f"Total box score games:  {len(boxscore_df)}")
print(f"Matched games:          {matched_count}")
print(f"Doubleheader games:     {duplicate_matches}")
print(f"Unmatched games:        {unmatched_count}")
print(f"Match rate:             {(matched_count + duplicate_matches)/len(boxscore_df)*100:.1f}%")

# Keep ALL games (don't filter)
print()
print(f"📊 Keeping ALL games: {len(boxscore_df)} games (matched: {matched_count + duplicate_matches}, unmatched: {unmatched_count})")

# Drop the temporary date_clean column
boxscore_df = boxscore_df.drop('date_clean', axis=1)

# Reorder columns to put balldontlie_game_id first
cols = boxscore_df.columns.tolist()
cols.remove('balldontlie_game_id')
cols = ['balldontlie_game_id'] + cols
boxscore_df = boxscore_df[cols]

print()
print("=" * 80)
print("Saving Updated Files")
print("=" * 80)

# Group by date and save
saved_files = 0
for date_str, group in boxscore_df.groupby('date'):
    output_file = f"{BOXSCORE_DIR}/boxscores_{date_str}.csv"
    group.to_csv(output_file, index=False)
    saved_files += 1
    if saved_files <= 5 or saved_files % 50 == 0:
        print(f"✅ Saved {date_str}: {len(group)} game(s)")

print()
print(f"✅ Updated {saved_files} files")

print()
print("=" * 80)
print("Verification")
print("=" * 80)

# Verify a sample file
sample_file = f"{BOXSCORE_DIR}/boxscores_2025-03-18.csv"
sample_df = pd.read_csv(sample_file)
print(f"Sample file: {sample_file}")
print(f"Columns: {len(sample_df.columns)}")
print(f"First column: {sample_df.columns[0]}")
print(f"Has balldontlie_game_id: {'balldontlie_game_id' in sample_df.columns}")
print()
print("Sample row:")
print(sample_df[['balldontlie_game_id', 'id', 'date', 'away_team_abbreviation', 'home_team_abbreviation']].head(1).to_string(index=False))

print()
print("=" * 80)
print("✅ COMPLETE")
print("=" * 80)
print(f"Box score files now have 'balldontlie_game_id' column")
print(f"Total games in updated files: {len(boxscore_df)}")
print(f"Games with balldontlie_game_id: {matched_count + duplicate_matches}")
print(f"Games without balldontlie_game_id: {unmatched_count}")
print(f"Column count per file: {len(boxscore_df.columns)}")
print("=" * 80)
