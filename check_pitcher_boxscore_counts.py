import pandas as pd
import glob

print("="*80)
print("CHECKING GAME COUNTS IN STARTING PITCHER BOXSCORE FILES (2010-2024)")
print("="*80)
print()

for year in range(2010, 2025):
    pitcher_path = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores'
    
    pitcher_files = sorted(glob.glob(f'{pitcher_path}/starting_pitcher_boxscores_*.csv'))
    
    if not pitcher_files:
        print(f"{year}: ⚠️  No starting pitcher boxscore files found")
        continue
    
    total_games = 0
    for file in pitcher_files:
        df = pd.read_csv(file)
        total_games += len(df)
    
    num_dates = len(pitcher_files)
    
    # Expected games (approximate)
    if year == 2020:
        expected = 900  # COVID-shortened season
    else:
        expected = 2430  # Normal season
    
    diff = total_games - expected
    status = "✓" if abs(diff) < 100 else "⚠️"
    
    print(f"{year}: {status} {total_games:,} games across {num_dates} dates (expected ~{expected:,}, diff: {diff:+,})")

print()
print("="*80)
