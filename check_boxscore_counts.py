import pandas as pd
import glob

print("="*80)
print("CHECKING GAME COUNTS IN BOXSCORE FILES (2010-2024)")
print("="*80)
print()

for year in range(2010, 2025):
    boxscore_path = f'data/{year}_data/mlb_data/raw/boxscores'
    
    boxscore_files = sorted(glob.glob(f'{boxscore_path}/boxscores_*.csv'))
    
    if not boxscore_files:
        print(f"{year}: ⚠️  No boxscore files found")
        continue
    
    total_games = 0
    for file in boxscore_files:
        df = pd.read_csv(file)
        total_games += len(df)
    
    num_dates = len(boxscore_files)
    
    # Expected games (approximate)
    if year == 2020:
        expected = 900  # COVID-shortened season (60 games × 30 teams / 2)
    else:
        expected = 2430  # Normal season (162 games × 30 teams / 2)
    
    diff = total_games - expected
    status = "✓" if abs(diff) < 100 else "⚠️"
    
    print(f"{year}: {status} {total_games:,} games across {num_dates} dates (expected ~{expected:,}, diff: {diff:+,})")

print()
print("="*80)
