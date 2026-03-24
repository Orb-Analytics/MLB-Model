import pandas as pd
import glob

print('Year | Boxscores | Pitchers | Missing')
print('-----|-----------|----------|---------')

for year in range(2010, 2025):
    try:
        # Count boxscores
        boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
        if boxscore_files:
            boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
            total_games = len(pd.concat(boxscore_dfs, ignore_index=True))
        else:
            total_games = 0
        
        # Count starting pitcher boxscores
        pitcher_files = glob.glob(f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/*.csv')
        if pitcher_files:
            pitcher_dfs = [pd.read_csv(f) for f in pitcher_files]
            total_pitchers = len(pd.concat(pitcher_dfs, ignore_index=True))
        else:
            total_pitchers = 0
        
        missing = total_games - total_pitchers
        status = '' if missing == 0 else ' ⚠️'
        print(f'{year} | {total_games:9} | {total_pitchers:8} | {missing:7}{status}')
    except Exception as e:
        print(f'{year} | Error: {str(e)}')
