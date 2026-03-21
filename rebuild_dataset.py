#!/usr/bin/env python3
"""
Rebuild the dataset from 4 CSVs (excluding boxscores)
Order: game_outlook, team_season_standings, starting_pitcher_stats, team_season_stats
"""

import pandas as pd

print("="*80)
print("REBUILDING DATASET FROM 4 ALIGNED CSVs")
print("="*80)

# Load all 4 datasets
print("\nLoading datasets...")
game_outlook = pd.read_csv('data/bdl_data/game_outlook.csv')
standings = pd.read_csv('data/bdl_data/team_season_standings.csv')
pitchers = pd.read_csv('data/bdl_data/starting_pitcher_stats.csv')
team_stats = pd.read_csv('data/bdl_data/team_season_stats.csv')

print(f"Game Outlook: {len(game_outlook)} rows, {len(game_outlook.columns)} columns")
print(f"Team Standings: {len(standings)} rows, {len(standings.columns)} columns")
print(f"Starting Pitchers: {len(pitchers)} rows, {len(pitchers.columns)} columns")
print(f"Team Season Stats: {len(team_stats)} rows, {len(team_stats.columns)} columns")

# Verify alignment by checking game IDs
print("\n" + "="*80)
print("VERIFYING ALIGNMENT BY GAME IDs")
print("="*80)

outlook_ids = game_outlook['id'].tolist()
standings_ids = standings['balldontlie_game_id'].tolist()
pitchers_ids = pitchers['balldontlie_game_id'].tolist()
team_stats_ids = team_stats['balldontlie_game_id'].tolist()

# Check if all match
misaligned = 0
for i in range(len(outlook_ids)):
    if not (outlook_ids[i] == standings_ids[i] == pitchers_ids[i] == team_stats_ids[i]):
        misaligned += 1
        if misaligned <= 5:  # Show first 5 mismatches
            print(f"Row {i+1}: outlook={outlook_ids[i]}, standings={standings_ids[i]}, pitchers={pitchers_ids[i]}, team_stats={team_stats_ids[i]}")

if misaligned == 0:
    print("✓✓✓ PERFECT ALIGNMENT! All game IDs match across all 4 datasets!")
else:
    print(f"\n❌ Found {misaligned} misaligned rows")
    print("Cannot proceed with merge until alignment is fixed.")
    exit(1)

# Merge datasets by concatenating columns (since rows already align perfectly)
print("\n" + "="*80)
print("MERGING DATASETS (CONCATENATING COLUMNS)")
print("="*80)

# Start with game_outlook
merged = game_outlook.copy()
print(f"Starting with Game Outlook: {len(merged.columns)} columns")

# Add standings columns (drop the duplicate game_id column)
standings_to_add = standings.drop(columns=['balldontlie_game_id'])
merged = pd.concat([merged, standings_to_add], axis=1)
print(f"After adding Standings: {len(merged.columns)} columns")

# Add pitcher columns (drop the duplicate game_id column)
pitchers_to_add = pitchers.drop(columns=['balldontlie_game_id'])
merged = pd.concat([merged, pitchers_to_add], axis=1)
print(f"After adding Starting Pitchers: {len(merged.columns)} columns")

# Add team stats columns (drop the duplicate game_id column)
team_stats_to_add = team_stats.drop(columns=['balldontlie_game_id'])
merged = pd.concat([merged, team_stats_to_add], axis=1)
print(f"After adding Team Season Stats: {len(merged.columns)} columns")

print(f"\n✓ Merged dataset: {len(merged)} rows × {len(merged.columns)} columns")

# Identify duplicate column names
print("\n" + "="*80)
print("IDENTIFYING DUPLICATE/REPETITIVE COLUMNS")
print("="*80)

# Find columns that appear multiple times (pandas adds .1, .2, etc.)
import re
column_base_names = {}
for col in merged.columns:
    # Remove .1, .2, etc. suffixes
    base_name = re.sub(r'\.\d+$', '', col)
    if base_name not in column_base_names:
        column_base_names[base_name] = []
    column_base_names[base_name].append(col)

duplicate_groups = {base: cols for base, cols in column_base_names.items() if len(cols) > 1}

if duplicate_groups:
    print(f"\nFound {len(duplicate_groups)} column names that appear multiple times:")
    for base, cols in sorted(duplicate_groups.items())[:20]:
        print(f"  {base}: {cols}")
    
    if len(duplicate_groups) > 20:
        print(f"  ... and {len(duplicate_groups) - 20} more")
    
    print(f"\nTotal duplicate columns: {sum(len(cols) - 1 for cols in duplicate_groups.values())}")
else:
    print("\n✓ No duplicate column names found")

# Save the merged dataset (before removing duplicates)
print("\n" + "="*80)
print("SAVING MERGED DATASET (WITH DUPLICATES)")
print("="*80)

output_path = 'data/bdl_data/2025_bdl_dataset_with_duplicates.csv'
merged.to_csv(output_path, index=False)
print(f"\n✓ Saved: {output_path}")
print(f"  Rows: {len(merged)}")
print(f"  Columns: {len(merged.columns)}")

# Show column structure
print("\n" + "="*80)
print("DATASET STRUCTURE")
print("="*80)

print("\nColumn order (first 40):")
for i, col in enumerate(merged.columns[:40], 1):
    print(f"  {i:3d}. {col}")

if len(merged.columns) > 40:
    print(f"  ... and {len(merged.columns) - 40} more columns")

print("\n" + "="*80)
print("✓✓✓ DATASET REBUILT! ✓✓✓")
print("="*80)
print("\nNext steps:")
print("  1. Review duplicate columns")
print("  2. Decide which duplicates to keep/remove")
print("  3. Create final cleaned version")
print("="*80)
