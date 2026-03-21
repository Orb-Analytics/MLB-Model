#!/usr/bin/env python3
"""
Investigate the structure of stats in early season games
"""

import pandas as pd

print("="*80)
print("INVESTIGATING EARLY SEASON STATS")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f"\nDataset: {len(df)} rows")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")

# Look at first few games for a specific team
test_team_id = 108  # Pick a team
print(f"\n{'='*80}")
print(f"EXAMINING TEAM {test_team_id} - FIRST 10 GAMES")
print(f"{'='*80}")

# Get games for this team (as home team)
team_games = df[df['home_team_id'] == test_team_id].sort_values('date').head(10)

print("\nShowing key stats for first 10 home games:")
print(f"{'Game':<6} {'Date':<12} {'GP':<5} {'Batting OPS':<12} {'Batting R':<10} {'Pitching ERA':<12}")
print("-"*80)

for idx, row in team_games.iterrows():
    game_num = idx + 1
    date = row['date'].strftime('%Y-%m-%d')
    gp = row['home_gp']
    ops = row['home_batting_ops']
    r = row['home_batting_r']
    era = row['home_pitching_era']
    
    print(f"{game_num:<6} {date:<12} {gp:<5.0f} {ops:<12.3f} {r:<10.0f} {era:<12.3f}")

# Check if stats are cumulative or per-game
print("\n" + "="*80)
print("ANALYSIS: Are these cumulative season stats?")
print("="*80)

team_games = df[df['home_team_id'] == test_team_id].sort_values('date').head(20)

print("\nChecking if batting_r (runs) increases each game (cumulative):")
print(f"{'Game':<6} {'Date':<12} {'GP':<5} {'Runs':<10} {'HR':<6} {'Hits':<8}")
print("-"*80)

for i, (idx, row) in enumerate(team_games.iterrows(), 1):
    date = row['date'].strftime('%Y-%m-%d')
    gp = row['home_gp']
    r = row['home_batting_r']
    hr = row['home_batting_hr']
    h = row['home_batting_h']
    
    print(f"{i:<6} {date:<12} {gp:<5.0f} {r:<10.0f} {hr:<6.0f} {h:<8.0f}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("\nIf runs/HR/hits increase each game → These are CUMULATIVE season stats")
print("If they vary up and down → These are per-game stats")
print("\nFor rolling averages to work correctly with cumulative stats,")
print("we need to compute the DIFFERENCE between consecutive games.")
