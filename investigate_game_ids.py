#!/usr/bin/env python3
"""
Investigate which game IDs are in which datasets
"""

import pandas as pd

# Load all datasets
outlook = pd.read_csv('data/bdl_data/game_outlook.csv')
boxscores = pd.read_csv('data/bdl_data/boxscores.csv')

outlook_ids = set(outlook['id'].values)
boxscores_ids = set(boxscores['balldontlie_game_id'].values)

print(f"Game Outlook: {len(outlook)} rows, {len(outlook_ids)} unique game IDs")
print(f"Box Scores: {len(boxscores)} rows, {len(boxscores_ids)} unique game IDs")

# Find differences
only_outlook = outlook_ids - boxscores_ids
only_boxscores = boxscores_ids - outlook_ids

print(f"\nGame IDs ONLY in Outlook: {len(only_outlook)}")
if only_outlook:
    print(f"  {sorted(only_outlook)}")

print(f"\nGame IDs ONLY in Box Scores: {len(only_boxscores)}")
if only_boxscores:
    print(f"  {sorted(only_boxscores)}")

# Check duplicates in each
outlook_dupes = outlook[outlook.duplicated(subset=['id'], keep=False)]
boxscores_dupes = boxscores[boxscores.duplicated(subset=['balldontlie_game_id'], keep=False)]

print(f"\nDuplicate game IDs in Outlook: {len(outlook_dupes)}")
if len(outlook_dupes) > 0:
    print(outlook_dupes[['id']].drop_duplicates().sort_values('id'))

print(f"\nDuplicate game IDs in Box Scores: {len(boxscores_dupes)}")
if len(boxscores_dupes) > 0:
    dupe_ids = boxscores_dupes['balldontlie_game_id'].unique()
    print(f"Game IDs that appear more than once: {sorted(dupe_ids)}")
    
    # Show details for each duplicate
    for game_id in sorted(dupe_ids)[:10]:  # Show first 10
        rows = boxscores[boxscores['balldontlie_game_id'] == game_id]
        print(f"\nGame {game_id}: {len(rows)} occurrences")
        if 'date' in rows.columns:
            print(f"  Dates: {rows['date'].tolist()}")
