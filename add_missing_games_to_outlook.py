#!/usr/bin/env python3
"""
Add the 8 matched missing games to the 2011 BDL game outlook files.
"""

import pandas as pd
import os
from datetime import datetime
import shutil

# Load the matched games
matched_games = pd.read_csv('matched_missing_2011_games.csv')

print("=" * 80)
print("Adding 8 Missing Games to 2011 BDL Game Outlook Files")
print("=" * 80)

# Group by date
matched_games['date_str'] = pd.to_datetime(matched_games['date']).dt.strftime('%Y-%m-%d')

outlook_dir = 'data/2011_data/mlb_data/raw/bdl_data/game_outlook'

# Create backup
backup_dir = f'{outlook_dir}/backup_before_adding_missing_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f"\n📁 Creating backup: {backup_dir}")
os.makedirs(backup_dir, exist_ok=True)

games_added = 0

for date_str, games_group in matched_games.groupby('date_str'):
    outlook_file = f'{outlook_dir}/game_outlook_{date_str}.csv'
    
    if not os.path.exists(outlook_file):
        print(f"\n⚠️  File not found: {outlook_file}")
        print(f"   Creating new file...")
        # If file doesn't exist, create it with just these games
        games_to_add = games_group.drop(columns=['date_str', 'mlb_game_pk']).copy()
        games_to_add.to_csv(outlook_file, index=False)
        games_added += len(games_to_add)
        print(f"   ✅ Created {outlook_file} with {len(games_to_add)} games")
        continue
    
    # Backup original file
    backup_file = f'{backup_dir}/game_outlook_{date_str}.csv'
    shutil.copy2(outlook_file, backup_file)
    
    # Load existing file
    existing_df = pd.read_csv(outlook_file)
    
    print(f"\n📅 {date_str}")
    print(f"   Current games in file: {len(existing_df)}")
    print(f"   Games to add: {len(games_group)}")
    
    # Prepare games to add (remove helper columns)
    games_to_add = games_group.drop(columns=['date_str', 'mlb_game_pk']).copy()
    
    # Check if any games are already in the file (by ID)
    existing_ids = set(existing_df['id'].tolist())
    new_games = games_to_add[~games_to_add['id'].isin(existing_ids)]
    
    if len(new_games) == 0:
        print(f"   ⚠️  All games already exist in file")
        continue
    
    # Check for games we thought would be new but are already there
    duplicates = games_to_add[games_to_add['id'].isin(existing_ids)]
    if len(duplicates) > 0:
        print(f"   ℹ️  {len(duplicates)} games already in file (skipping):")
        for _, dup in duplicates.iterrows():
            print(f"      ID {dup['id']}: {dup['away_team_abbreviation']} @ {dup['home_team_abbreviation']}")
    
    # Append new games
    combined_df = pd.concat([existing_df, new_games], ignore_index=True)
    
    # Ensure column order matches
    combined_df = combined_df[existing_df.columns]
    
    # Save updated file
    combined_df.to_csv(outlook_file, index=False)
    
    games_added += len(new_games)
    print(f"   ✅ Added {len(new_games)} games")
    print(f"   New total: {len(combined_df)} games")
    
    # Show which games were added
    for _, game in new_games.iterrows():
        print(f"      • ID {game['id']}: {game['away_team_abbreviation']} @ {game['home_team_abbreviation']} ({game['away_team_score']}-{game['home_team_score']})")

print("\n" + "=" * 80)
print("Summary:")
print("=" * 80)
print(f"✅ Added {games_added} games to outlook files")
print(f"📁 Backup created: {backup_dir}")

# Verify final counts
print("\nVerifying game counts...")
outlook_files = sorted([f for f in os.listdir(outlook_dir) if f.startswith('game_outlook_') and f.endswith('.csv')])
total_games = sum(len(pd.read_csv(f'{outlook_dir}/{f}')) for f in outlook_files)

print(f"\nTotal games in 2011 game outlook: {total_games}")
print(f"Expected: 2430")
print(f"Difference: {2430 - total_games}")

if total_games == 2430:
    print("\n🎉 SUCCESS! All 2430 games are now present!")
else:
    print(f"\n⚠️  Still missing {2430 - total_games} games")
