#!/usr/bin/env python3
"""
Check if starting pitcher stats are correctly aligned with their games
"""

import pandas as pd

print("="*80)
print("INVESTIGATING STARTING PITCHER STATS ALIGNMENT")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print(f"\nLoaded dataset: {len(df)} rows × {len(df.columns)} columns")

# Find starting pitcher columns
sp_cols = [col for col in df.columns if 'starting_pitcher' in col.lower() or 'starter_pitching' in col.lower()]
print(f"\nFound {len(sp_cols)} starting pitcher related columns")

# Sample a few
print("\nSample starting pitcher columns:")
for col in sorted(sp_cols)[:15]:
    print(f"  {col}")

# Look at first few games for a specific team
print("\n" + "="*80)
print("EXAMINING FIRST 10 GAMES FOR A SAMPLE TEAM")
print("="*80)

# Get first team
first_team_id = df['home_team_id'].iloc[0]
team_games = df[(df['home_team_id'] == first_team_id) | (df['away_team_id'] == first_team_id)].head(10)

print(f"\nTeam ID: {first_team_id}")
print(f"Season games: {len(team_games)}")

for i, (idx, row) in enumerate(team_games.iterrows(), 1):
    is_home = row['home_team_id'] == first_team_id
    prefix = 'home' if is_home else 'away'
    
    print(f"\n{'='*60}")
    print(f"Game #{i} - {row['date'].date()} - {'Home' if is_home else 'Away'}")
    print(f"{'='*60}")
    
    # Show GP (cumulative games played by this team entering this game)
    gp_col = f'{prefix}_gp'
    if gp_col in row.index:
        print(f"GP (cumulative): {row[gp_col]}")
    
    # Show some starting pitcher base stats
    print("\nStarting Pitcher Base Stats:")
    base_stats = ['starter_pitching_gs', 'starter_pitching_qs', 'pitching_ip', 'pitching_era']
    for stat in base_stats:
        col = f'{prefix}_{stat}'
        if col in row.index:
            print(f"  {stat}: {row[col]}")
    
    # Show derived starting pitcher stats
    print("\nDerived Starting Pitcher Stats:")
    derived_stats = ['starting_pitcher_qs_rate', 'starting_pitcher_ip_per_gs', 'starting_pitcher_k_bb_ratio']
    for stat in derived_stats:
        col = f'{prefix}_{stat}'
        if col in row.index:
            print(f"  {stat}: {row[col]}")

# Check if there's a pattern: are GP=1 games showing non-zero pitcher stats?
print("\n" + "="*80)
print("CHECKING FOR MISALIGNMENT: GP=1 GAMES WITH NON-ZERO PITCHER STATS")
print("="*80)

for prefix in ['home', 'away']:
    gp_col = f'{prefix}_gp'
    
    if gp_col in df.columns:
        # Get games where GP=1 (team's first game of season)
        first_games = df[df[gp_col] == 1]
        
        print(f"\n{prefix.upper()} teams - First games (GP=1): {len(first_games)} games")
        
        if len(first_games) > 0:
            # Check starting pitcher stats in these first games
            sample = first_games.iloc[0]
            
            print(f"\nSample first game:")
            print(f"  Date: {sample['date']}")
            print(f"  Team: {sample[f'{prefix}_team_id']}")
            print(f"  GP: {sample[gp_col]}")
            
            # Check pitcher stats
            sp_stat_cols = [col for col in df.columns if col.startswith(f'{prefix}_') and 'pitching' in col]
            
            print(f"\n  Pitcher stats in first game:")
            non_zero_count = 0
            for col in sorted(sp_stat_cols)[:10]:
                val = sample[col]
                if pd.notna(val) and val != 0:
                    print(f"    {col}: {val}")
                    non_zero_count += 1
            
            if non_zero_count == 0:
                print(f"    All pitcher stats are 0 or NaN (EXPECTED for GP=1)")
            else:
                print(f"    ⚠️  Found {non_zero_count} non-zero pitcher stats in GP=1 game!")
                print(f"    This suggests stats might be misaligned!")

# Check the alignment logic: do stats represent ENTERING the game or AFTER the game?
print("\n" + "="*80)
print("UNDERSTANDING STAT TIMING")
print("="*80)

print("\nThe key question: When GP=5, does that mean:")
print("  A) Team has played 4 games and is about to play their 5th?")
print("  B) Team has completed 5 games?")

# Look at a sequence of games for one team
sample_team = df['home_team_id'].iloc[0]
sample_games = df[(df['home_team_id'] == sample_team) | (df['away_team_id'] == sample_team)].head(5)

print(f"\nLooking at first 5 games for team {sample_team}:")
for idx, (_, row) in enumerate(sample_games.iterrows(), 1):
    is_home = row['home_team_id'] == sample_team
    prefix = 'home' if is_home else 'away'
    gp = row[f'{prefix}_gp']
    
    print(f"  Game {idx}: GP={gp}")

print("\nIf GP increases from 1->2->3->4->5, then GP represents games COMPLETED")
print("This means GP=1 is their FIRST game, and stats should be mostly 0")

print("\n" + "="*80)
