#!/usr/bin/env python3
"""
Fix stat alignment by shifting team stats back one game
Stats should represent what the team's stats were ENTERING the game, not after
"""

import pandas as pd
import numpy as np

print("="*80)
print("FIXING STAT ALIGNMENT - SHIFTING TEAM STATS BACK ONE GAME")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f"\nLoaded dataset: {len(df)} rows × {len(df.columns)} columns")

# Identify columns that should be shifted (all team stats except identifiers)
columns_to_keep_unshifted = [
    'balldontlie_game_id',
    'id', 
    'date',
    'home_team_id',
    'away_team_id',
    'home_team_abbreviation',
    'away_team_abbreviation',
    'home_team_display_name',
    'away_team_display_name',
    'home_team_name',
    'away_team_name',
    'home_postseason',
    'away_postseason',
    'home_season_type',
    'away_season_type',
    'home_season',
    'away_season',
]

print("\n" + "="*80)
print("IDENTIFYING COLUMNS TO SHIFT")
print("="*80)

# All stat columns need to be shifted back (they represent AFTER game, we need BEFORE)
stat_columns_home = [col for col in df.columns if col.startswith('home_') and col not in columns_to_keep_unshifted]
stat_columns_away = [col for col in df.columns if col.startswith('away_') and col not in columns_to_keep_unshifted]

print(f"\nHome team stat columns to shift: {len(stat_columns_home)}")
print(f"Away team stat columns to shift: {len(stat_columns_away)}")
print(f"Total columns to shift: {len(stat_columns_home) + len(stat_columns_away)}")

# Show sample columns being shifted
print("\nSample columns being shifted:")
for col in sorted(stat_columns_home)[:10]:
    print(f"  {col}")

print("\n" + "="*80)
print("SHIFTING STATS BACK ONE GAME PER TEAM")
print("="*80)

# Create new dataframe with unshifted columns
df_fixed = df[columns_to_keep_unshifted].copy()

# Get unique teams
all_teams = sorted(set(df['home_team_id'].unique()) | set(df['away_team_id'].unique()))
print(f"\nProcessing {len(all_teams)} teams...")

# Initialize stat columns with NaN
for col in stat_columns_home + stat_columns_away:
    df_fixed[col] = np.nan

# Process each team separately
for team_id in all_teams:
    # Get all games for this team (both home and away), sorted by date
    home_mask = df['home_team_id'] == team_id
    away_mask = df['away_team_id'] == team_id
    
    team_games_home_idx = df[home_mask].sort_values('date').index
    team_games_away_idx = df[away_mask].sort_values('date').index
    
    # Shift home games stats
    if len(team_games_home_idx) > 0:
        # For each stat column, get values and shift them
        for col in stat_columns_home:
            if col in df.columns:
                # Get the values in chronological order
                values = df.loc[team_games_home_idx, col].values
                # Shift: prepend NaN, drop last value
                shifted_values = np.concatenate([[np.nan], values[:-1]])
                # Store in fixed dataframe
                df_fixed.loc[team_games_home_idx, col] = shifted_values
    
    # Shift away games stats
    if len(team_games_away_idx) > 0:
        for col in stat_columns_away:
            if col in df.columns:
                values = df.loc[team_games_away_idx, col].values
                shifted_values = np.concatenate([[np.nan], values[:-1]])
                df_fixed.loc[team_games_away_idx, col] = shifted_values

print("  ✓ Stats shifted back one game for all teams")

print("\n" + "="*80)
print("VERIFICATION")
print("="*80)

# Check first game for a team - should now be all NaN
first_team = df_fixed['home_team_id'].iloc[0]
first_game = df_fixed[df_fixed['home_team_id'] == first_team].iloc[0]

print(f"\nFirst game for team {first_team}:")
print(f"  Date: {first_game['date']}")

# Check some stat columns
sample_stats = ['home_pitching_k_bb_ratio', 'home_batting_ops_rolling_10', 'home_starter_pitching_gs']
print(f"  Stats (should be NaN for first game):")
for stat in sample_stats:
    if stat in first_game.index:
        val = first_game[stat]
        is_nan = pd.isna(val)
        print(f"    {stat}: {val} {'✓ (NaN)' if is_nan else '❌ (should be NaN)'}")

# Check second game - should have first game's stats
second_game = df_fixed[df_fixed['home_team_id'] == first_team].iloc[1]
print(f"\nSecond game for team {first_team}:")
print(f"  Date: {second_game['date']}")
print(f"  Stats (should have values from first game):")
for stat in sample_stats:
    if stat in second_game.index:
        val = second_game[stat]
        is_nan = pd.isna(val)
        print(f"    {stat}: {val} {'(has value)' if not is_nan else '(NaN)'}")

# Count how many games now have NaN stats (should be 30 teams × ~2 first games = ~60)
print("\n" + "="*80)
print("STATS SUMMARY")
print("="*80)

# Check a sample stat column
sample_col = 'home_pitching_k_bb_ratio'
if sample_col in df_fixed.columns:
    before_nan = df[sample_col].isna().sum()
    after_nan = df_fixed[sample_col].isna().sum()
    
    print(f"\n{sample_col}:")
    print(f"  Before shift: {before_nan} NaN values")
    print(f"  After shift: {after_nan} NaN values")
    print(f"  Difference: +{after_nan - before_nan} NaN values (expected ~30 for first games)")

print(f"\nNew dataset size: {len(df_fixed)} rows × {len(df_fixed.columns)} columns")

# Save the fixed dataset
print("\n" + "="*80)
print("SAVING FIXED DATASET")
print("="*80)

df_fixed.to_csv('data/bdl_data/2025_bdl_dataset.csv', index=False)
print(f"\n✓ Saved: data/bdl_data/2025_bdl_dataset.csv")
print(f"  Rows: {len(df_fixed)}")
print(f"  Columns: {len(df_fixed.columns)}")

print("\n✓✓✓ STAT ALIGNMENT FIXED! ✓✓✓")
print("Stats now represent ENTERING the game, not AFTER")
print("="*80)
