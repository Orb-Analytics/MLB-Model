#!/usr/bin/env python3
"""
Merge the 4 datasets (boxscores, standings, pitchers, team stats) into one master dataset
"""

import pandas as pd

print("="*80)
print("MERGING 4 DATASETS INTO 2025_bdl_dataset.csv")
print("="*80)

# Load all 4 datasets
print("\nLoading datasets...")
boxscores = pd.read_csv('data/bdl_data/boxscores.csv')
standings = pd.read_csv('data/bdl_data/team_season_standings.csv')
pitchers = pd.read_csv('data/bdl_data/starting_pitcher_stats.csv')
team_stats = pd.read_csv('data/bdl_data/team_season_stats.csv')

print(f"Box Scores: {len(boxscores)} rows, {len(boxscores.columns)} columns")
print(f"Standings: {len(standings)} rows, {len(standings.columns)} columns")
print(f"Pitchers: {len(pitchers)} rows, {len(pitchers.columns)} columns")
print(f"Team Stats: {len(team_stats)} rows, {len(team_stats.columns)} columns")

# Verify they all have the same game IDs in the same order
print("\n" + "="*80)
print("VERIFYING ALIGNMENT...")
print("="*80)

box_ids = boxscores['balldontlie_game_id'].tolist()
stand_ids = standings['balldontlie_game_id'].tolist()
pitch_ids = pitchers['balldontlie_game_id'].tolist()
team_ids = team_stats['balldontlie_game_id'].tolist()

if box_ids == stand_ids == pitch_ids == team_ids:
    print("✓ All datasets perfectly aligned by game ID")
else:
    print("❌ ERROR: Datasets not aligned!")
    exit(1)

# Merge all datasets
print("\n" + "="*80)
print("MERGING DATASETS...")
print("="*80)

# Start with boxscores as the base
merged = boxscores.copy()
print(f"\nStarting with Box Scores: {len(merged.columns)} columns")

# Merge standings (use suffixes to handle any duplicate columns)
merged = merged.merge(
    standings,
    on='balldontlie_game_id',
    how='inner',
    suffixes=('', '_standings')
)
print(f"After adding Standings: {len(merged.columns)} columns")

# Merge pitchers
merged = merged.merge(
    pitchers,
    on='balldontlie_game_id',
    how='inner',
    suffixes=('', '_pitchers')
)
print(f"After adding Starting Pitchers: {len(merged.columns)} columns")

# Merge team stats
merged = merged.merge(
    team_stats,
    on='balldontlie_game_id',
    how='inner',
    suffixes=('', '_team_stats')
)
print(f"After adding Team Stats: {len(merged.columns)} columns")

print(f"\n✓ Final merged dataset: {len(merged)} rows × {len(merged.columns)} columns")

# Save the merged dataset
print("\n" + "="*80)
print("SAVING MERGED DATASET...")
print("="*80)

output_path = 'data/bdl_data/2025_bdl_dataset.csv'
merged.to_csv(output_path, index=False)
print(f"✓ Saved: {output_path}")
print(f"  Rows: {len(merged)}")
print(f"  Columns: {len(merged.columns)}")

# Show column summary
print("\n" + "="*80)
print("COLUMN SUMMARY")
print("="*80)
print(f"\nTotal columns: {len(merged.columns)}")
print("\nSample columns:")
for i, col in enumerate(merged.columns[:20]):
    print(f"  {i+1}. {col}")
if len(merged.columns) > 20:
    print(f"  ... and {len(merged.columns) - 20} more columns")

print("\n" + "="*80)
print("✓✓✓ MERGE COMPLETE! ✓✓✓")
print("="*80)
