import pandas as pd
import glob
import os

def count_records(year):
    """Count MLB boxscores and BDL game outlook records."""
    
    # Count MLB boxscores
    mlb_path = f'data/{year}_data/mlb_data/raw/boxscores/'
    mlb_count = None
    if os.path.exists(mlb_path):
        mlb_files = glob.glob(f'{mlb_path}*.csv')
        if mlb_files:
            mlb_dfs = [pd.read_csv(f) for f in mlb_files]
            mlb = pd.concat(mlb_dfs, ignore_index=True)
            mlb_count = len(mlb)
    
    # Count BDL game outlook
    bdl_path = f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/'
    bdl_count = None
    if os.path.exists(bdl_path):
        bdl_files = glob.glob(f'{bdl_path}*.csv')
        if bdl_files:
            bdl_dfs = [pd.read_csv(f) for f in bdl_files]
            bdl = pd.concat(bdl_dfs, ignore_index=True)
            bdl_count = len(bdl)
    
    return mlb_count, bdl_count

if __name__ == "__main__":
    print("Year | MLB Boxscores | BDL Game Outlook | Difference")
    print("-----|---------------|------------------|-----------")
    
    for year in range(2009, 2025):
        mlb_count, bdl_count = count_records(year)
        
        if mlb_count is not None and bdl_count is not None:
            diff = mlb_count - bdl_count
            diff_str = f"{diff:+d}" if diff != 0 else " 0"
            status = "✅" if diff == 0 else "⚠️"
            print(f"{year} | {mlb_count:13} | {bdl_count:16} | {diff_str:>5} {status}")
        elif mlb_count is not None:
            print(f"{year} | {mlb_count:13} | {'N/A':16} | {'N/A':>5}")
        elif bdl_count is not None:
            print(f"{year} | {'N/A':13} | {bdl_count:16} | {'N/A':>5}")
        else:
            print(f"{year} | {'N/A':13} | {'N/A':16} | {'N/A':>5}")
