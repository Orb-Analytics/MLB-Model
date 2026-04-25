#!/usr/bin/env python3
"""
Create properly aligned game_outlook from scratch to match box scores exactly
"""

import pandas as pd
import glob
from datetime import datetime

# Load box scores to use as the master template
print("Loading box scores as master template...")
boxscores = pd.read_csv('data/bdl_data/boxscores.csv')
print(f"Box scores: {len(boxscores)} rows")

# Get the list of game IDs and dates from box scores
master_games = boxscores[['balldontlie_game_id', 'date']].copy()
master_games = master_games.rename(columns={'balldontlie_game_id': 'game_id'})
print(f"\nMaster template created with {len(master_games)} games")

# Load all individual game_outlook files
print("\nLoading individual game_outlook files...")
outlook_files = sorted(glob.glob('data/bdl_data/game_outlook/game_outlook_*.csv'))
print(f"Found {len(outlook_files)} files")

all_outlook = []
for file in outlook_files:
    df = pd.read_csv(file)
    all_outlook.append(df)

outlook_combined = pd.concat(all_outlook, ignore_index=True)
print(f"Combined: {len(outlook_combined)} rows")

# Ensure we have unique game IDs in outlook (remove exact duplicates)
print("\nRemoving exact duplicates from outlook...")
outlook_unique = outlook_combined.drop_duplicates(subset=['id'], keep='first')
print(f"After deduplication: {len(outlook_unique)} unique games")

# Now create the aligned outlook byjoining with master template
print("\nAligning outlook to match box scores template...")
print(f"Master template has these game IDs:")
print(f"  Unique: {master_games['game_id'].nunique()}")
print(f"  Total rows: {len(master_games)}")

# For each row in master_games, find the matching outlook row
aligned_outlook = []

for idx, row in master_games.iterrows():
    game_id = row['game_id']
    date = row['date']
    
    # Find this game in outlook
    outlook_row = outlook_unique[outlook_unique['id'] == game_id]
    
    if len(outlook_row) == 0:
        print(f"  Warning: Game {game_id} not found in outlook")
        continue
    
    # Make a copy and set the date to match box scores
    outlook_copy = outlook_row.iloc[0].to_dict()
    outlook_copy['date'] = date  # Use box scores date for consistency
    aligned_outlook.append(outlook_copy)

aligned_outlook_df = pd.DataFrame(aligned_outlook)
print(f"\nAligned outlook created: {len(aligned_outlook_df)} rows")

# Verify alignment
print("\n" + "="*80)
print("VERIFICATION")
print("="*80)

outlook_ids = aligned_outlook_df['id'].tolist()
boxscores_ids = boxscores['balldontlie_game_id'].tolist()

print(f"Game Outlook: {len(outlook_ids)} rows")
print(f"Box Scores: {len(boxscores_ids)} rows")

if len(outlook_ids) != len(boxscores_ids):
    print(f"\n❌ Row count mismatch!")
else:
    mismatches = sum(1 for o, b in zip(outlook_ids, boxscores_ids) if o != b)
    
    if mismatches == 0:
        print("\n✓✓✓ PERFECT ALIGNMENT! All game IDs match! ✓✓✓")
        
        # Save the aligned outlook
        print("\nSaving aligned game_outlook.csv...")
        aligned_outlook_df.to_csv('data/bdl_data/game_outlook.csv', index=False)
        print(f"✓ Saved: {len(aligned_outlook_df)} rows")
    else:
        print(f"\n❌ Found {mismatches} mismatched game IDs")
        # Show first few mismatches
        for i, (o, b) in enumerate(zip(outlook_ids, boxscores_ids)):
            if o != b:
                print(f"  Row {i+1}: outlook={o}, boxscores={b}")
                if i > 10:
                    break

print("\n" + "="*80)
