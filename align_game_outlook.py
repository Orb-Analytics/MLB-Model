#!/usr/bin/env python3
"""
Align game_outlook to match the other 4 datasets:
- Remove 4 cancelled games (never played, no box scores)
- Duplicate 4 postponed games (to match how box scores has them twice)
Result: Same 2,430 rows with same game IDs in same order
"""

import pandas as pd
import glob

# Games that were scheduled but never played (no box scores exist)
CANCELLED_GAMES = [14693, 31102, 50869, 64546]

# Postponed games that appear twice in box scores (original + rescheduled date)
POSTPONED_GAMES = {
    14532: ['2025-05-09', '2025-05-10'],
    31235: ['2025-07-05', '2025-07-06'],
    50226: ['2025-09-08', '2025-09-10'],
    64541: ['2025-05-21', '2025-05-22']
}

print("="*80)
print("ALIGNING GAME_OUTLOOK TO MATCH OTHER 4 DATASETS")
print("="*80)

# Load game outlook
print("\nLoading game_outlook...")
outlook = pd.read_csv('data/bdl_data/game_outlook.csv')
print(f"Before: {len(outlook)} rows")

# Step 1: Remove cancelled games
print(f"\nStep 1: Removing {len(CANCELLED_GAMES)} cancelled games...")
for game_id in CANCELLED_GAMES:
    count_before = len(outlook)
    outlook = outlook[outlook['id'] != game_id]
    removed = count_before - len(outlook)
    if removed > 0:
        print(f"  Removed game {game_id}")
print(f"After removing cancelled: {len(outlook)} rows")

# Step 2: Duplicate postponed games
print(f"\nStep 2: Duplicating {len(POSTPONED_GAMES)} postponed games...")
rows_to_add = []

for game_id, dates in POSTPONED_GAMES.items():
    # Find the game in outlook
    game_row = outlook[outlook['id'] == game_id]
    
    if len(game_row) == 0:
        print(f"  ⚠ Warning: Game {game_id} not found in outlook")
        continue
    
    if len(game_row) > 1:
        print(f"  ⚠ Warning: Game {game_id} already appears {len(game_row)} times")
        continue
    
    # The game currently exists once at one of the two dates
    current_date = game_row.iloc[0]['date'] if 'date' in game_row.columns else None
    print(f"  Game {game_id}: Current date = {current_date}")
    
    # We need to add an entry for the OTHER date
    # Create a copy of the row for the other date
    for date in dates:
        if date != current_date:
            new_row = game_row.copy()
            new_row['date'] = date
            rows_to_add.append(new_row)
            print(f"    Adding duplicate at date {date}")

if rows_to_add:
    outlook = pd.concat([outlook] + rows_to_add, ignore_index=True)
    print(f"\nAfter adding postponed duplicates: {len(outlook)} rows")

# Step 3: Sort by date
print("\nStep 3: Sorting by date...")
if 'date' in outlook.columns:
    outlook = outlook.sort_values('date').reset_index(drop=True)
    print("✓ Sorted by date")
else:
    print("⚠ Warning: No 'date' column found")

# Step 4: Save
print("\nStep 4: Saving aligned game_outlook...")
outlook.to_csv('data/bdl_data/game_outlook.csv', index=False)
print(f"✓ Saved: {len(outlook)} rows")

# Step 5: Verify against box scores
print("\n" + "="*80)
print("VERIFICATION")
print("="*80)

boxscores = pd.read_csv('data/bdl_data/boxscores.csv')

outlook_ids = outlook['id'].tolist()
boxscores_ids = boxscores['balldontlie_game_id'].tolist()

print(f"\nGame Outlook: {len(outlook_ids)} rows")
print(f"Box Scores: {len(boxscores_ids)} rows")

if outlook_ids == boxscores_ids:
    print("\n✓✓✓ PERFECT MATCH! All game IDs match in exact order! ✓✓✓")
else:
    # Find mismatches
    mismatches = 0
    for i, (o_id, b_id) in enumerate(zip(outlook_ids, boxscores_ids)):
        if o_id != b_id:
            mismatches += 1
            if mismatches <= 10:
                print(f"Row {i+1}: outlook={o_id}, boxscores={b_id}")
    
    if mismatches > 10:
        print(f"... and {mismatches - 10} more mismatches")
    
    print(f"\n❌ Found {mismatches} mismatched rows")

print("\n" + "="*80)
