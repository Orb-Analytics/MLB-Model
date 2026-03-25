import pandas as pd

# Show alignment across ALL THREE datasets
date = '2011-04-01'

boxscore = pd.read_csv(f'data/2011_data/mlb_data/raw/boxscores/boxscores_{date}.csv')
pitcher = pd.read_csv(f'data/2011_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date}.csv')
outlook = pd.read_csv(f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv')

print("="*100)
print(f"THREE-WAY ALIGNMENT VERIFICATION: {date}")
print("="*100)

print(f"\n{'Row':<4} {'Boxscore':<10} {'Pitcher':<10} {'Outlook':<10} {'Match':<6} {'Matchup':<12} {'Score':<7} {'Away Starter':<20} {'Home Starter':<20}")
print("-" * 100)

all_match = True

for i in range(len(boxscore)):
    b_pk = boxscore.iloc[i]['game_pk']
    p_pk = pitcher.iloc[i]['game_pk']
    o_pk = outlook.iloc[i]['game_pk']
    
    match = "✓" if b_pk == p_pk == o_pk else "✗"
    if b_pk != p_pk or b_pk != o_pk:
        all_match = False
    
    # Get matchup and scores
    away = boxscore.iloc[i]['away_team_abbreviation']
    home = boxscore.iloc[i]['home_team_abbreviation']
    matchup = f"{away}@{home}"
    score = f"{int(boxscore.iloc[i]['away_batting_r'])}-{int(boxscore.iloc[i]['home_batting_r'])}"
    
    # Get starting pitchers
    away_starter = pitcher.iloc[i]['away_starter_name']
    home_starter = pitcher.iloc[i]['home_starter_name']
    
    print(f"{i:<4} {b_pk:<10} {p_pk:<10} {o_pk:<10} {match:<6} {matchup:<12} {score:<7} {away_starter:<20} {home_starter:<20}")

print("\n" + "="*100)
if all_match:
    print("✓ ALL GAME_PKS MATCH PERFECTLY ACROSS ALL THREE DATASETS!")
else:
    print("✗ Some game_pks don't match")
print("="*100)

# Show comprehensive stats
print("\n" + "="*100)
print("COMPREHENSIVE ALIGNMENT STATISTICS")
print("="*100)

import glob

boxscore_files = sorted(glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv'))
total_checked = 0
total_aligned = 0

for boxscore_file in boxscore_files:
    import os
    date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
    pitcher_file = f'data/2011_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date_str}.csv'
    outlook_file = f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date_str}.csv'
    
    if not all([os.path.exists(f) for f in [pitcher_file, outlook_file]]):
        continue
    
    b = pd.read_csv(boxscore_file)
    p = pd.read_csv(pitcher_file)
    o = pd.read_csv(outlook_file)
    
    for i in range(len(b)):
        total_checked += 1
        if b.iloc[i]['game_pk'] == p.iloc[i]['game_pk'] == o.iloc[i]['game_pk']:
            total_aligned += 1

print(f"\nTotal rows checked across all files: {total_checked}")
print(f"Perfectly aligned rows: {total_aligned}")
print(f"Misaligned rows: {total_checked - total_aligned}")
print(f"Success rate: {total_aligned/total_checked*100:.2f}%")

if total_aligned == total_checked:
    print("\n" + "🎉 " * 15)
    print("PERFECT THREE-WAY ALIGNMENT CONFIRMED!")
    print(f"All {total_checked} rows align perfectly across:")
    print("  1. Boxscores (game stats)")
    print("  2. Starting Pitcher Boxscores (pitcher details)")
    print("  3. Game Outlook (betting/venue info)")
    print("🎉 " * 15)

print("\n" + "="*100)
