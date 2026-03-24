import pandas as pd
import glob
import os

def count_bdl_game_outlook_records(year):
    """Count game outlook records for BDL data."""
    
    outlook_path = f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/'
    
    if not os.path.exists(outlook_path):
        return None, "Path does not exist"
    
    # Get all CSV files
    outlook_files = glob.glob(f'{outlook_path}*.csv')
    
    if not outlook_files:
        return 0, "No CSV files found"
    
    # Load and count
    try:
        outlook_dfs = [pd.read_csv(f) for f in outlook_files]
        outlook = pd.concat(outlook_dfs, ignore_index=True)
        return len(outlook), f"{len(outlook_files)} files"
    except Exception as e:
        return None, f"Error: {str(e)}"

if __name__ == "__main__":
    print("Year | BDL Game Outlook Records | Files")
    print("-----|--------------------------|------")
    
    total_records = 0
    years_with_data = 0
    
    for year in range(2009, 2025):
        count, info = count_bdl_game_outlook_records(year)
        
        if count is not None:
            print(f"{year} | {count:24} | {info}")
            total_records += count
            years_with_data += 1
        else:
            print(f"{year} | {'N/A':24} | {info}")
    
    print("-----|--------------------------|------")
    print(f"Total: {total_records} records across {years_with_data} years")
