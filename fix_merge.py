#!/usr/bin/env python3
"""
Investigate why merge created extra rows
"""

import pandas as pd

print("Investigating merge results...")

# Load all datasets
boxscores = pd.read_csv('data/bdl_data/boxscores.csv')
standings = pd.read_csv('data/bdl_data/team_season_standings.csv')
pitchers = pd.read_csv('data/bdl_data/starting_pitcher_stats.csv')
team_stats = pd.read_csv('data/bdl_data/team_season_stats.csv')

print(f"\nOriginal row counts:")
print(f"  Box Scores: {len(boxscores)}")
print(f"  Standings: {len(standings)}")
print(f"  Pitchers: {len(pitchers)}")
print(f"  Team Stats: {len(team_stats)}")

# Check for duplicate game IDs in each
print(f"\nDuplicate game IDs:")
print(f"  Box Scores: {boxscores['balldontlie_game_id'].duplicated().sum()}")
print(f"  Standings: {standings['balldontlie_game_id'].duplicated().sum()}")
print(f"  Pitchers: {pitchers['balldontlie_game_id'].duplicated().sum()}")
print(f"  Team Stats: {team_stats['balldontlie_game_id'].duplicated().sum()}")

# Check for duplicate columns that might cause issues
print(f"\nChecking for overlapping columns (besides game_id)...")

box_cols = set(boxscores.columns) - {'balldontlie_game_id'}
stand_cols = set(standings.columns) - {'balldontlie_game_id'}
pitch_cols = set(pitchers.columns) - {'balldontlie_game_id'}
team_cols = set(team_stats.columns) - {'balldontlie_game_id'}

# Find overlaps
box_stand = box_cols & stand_cols
box_pitch = box_cols & pitch_cols
box_team = box_cols & team_cols
stand_pitch = stand_cols & pitch_cols
stand_team = stand_cols & team_cols
pitch_team = pitch_cols & team_cols

if box_stand:
    print(f"\nBox Scores & Standings overlap: {len(box_stand)} columns")
    print(f"  {sorted(list(box_stand))[:10]}")
if box_pitch:
    print(f"\nBox Scores & Pitchers overlap: {len(box_pitch)} columns")
    print(f"  {sorted(list(box_pitch))[:10]}")
if box_team:
    print(f"\nBox Scores & Team Stats overlap: {len(box_team)} columns")
    print(f"  {sorted(list(box_team))[:10]}")
if stand_pitch:
    print(f"\nStandings & Pitchers overlap: {len(stand_pitch)} columns")
    print(f"  {sorted(list(stand_pitch))[:10]}")
if stand_team:
    print(f"\nStandings & Team Stats overlap: {len(stand_team)} columns")
    print(f"  {sorted(list(stand_team))[:10]}")
if pitch_team:
    print(f"\nPitchers & Team Stats overlap: {len(pitch_team)} columns")
    print(f"  {sorted(list(pitch_team))[:10]}")

# Try a simple concatenation instead
print("\n" + "="*80)
print("Trying concatenation approach instead of merge...")
print("="*80)

# Drop balldontlie_game_id from all except the first
boxscores_clean = boxscores.copy()
standings_clean = standings.drop(columns=['balldontlie_game_id'])
pitchers_clean = pitchers.drop(columns=['balldontlie_game_id'])
team_stats_clean = team_stats.drop(columns=['balldontlie_game_id'])

# Concatenate horizontally
merged_concat = pd.concat([boxscores_clean, standings_clean, pitchers_clean, team_stats_clean], axis=1)

print(f"\nConcatenation result: {len(merged_concat)} rows × {len(merged_concat.columns)} columns")

if len(merged_concat) == 2430:
    print("✓ Correct row count with concatenation!")
    
    # Save this version
    merged_concat.to_csv('data/bdl_data/2025_bdl_dataset.csv', index=False)
    print(f"\n✓ Saved corrected dataset: data/bdl_data/2025_bdl_dataset.csv")
    print(f"  Rows: {len(merged_concat)}")
    print(f"  Columns: {len(merged_concat.columns)}")
else:
    print(f"❌ Still wrong: {len(merged_concat)} rows")
