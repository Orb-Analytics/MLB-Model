import pandas as pd
import glob

def compare_boxscores_and_outlook(year):
    """Compare MLB boxscores with BDL game outlook files for a specific year."""
    
    print(f"\n{'='*80}")
    print(f"Comparing Boxscores and Game Outlook for {year}")
    print('='*80)
    
    # Load MLB boxscores
    boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
    if not boxscore_files:
        print(f"No boxscore files found for {year}")
        return
    
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    print(f"MLB Boxscores: {len(boxscores)} games")
    
    # Load BDL game outlook
    outlook_files = glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv')
    if not outlook_files:
        print(f"No game outlook files found for {year}")
        return
    
    outlook_dfs = [pd.read_csv(f) for f in outlook_files]
    outlook = pd.concat(outlook_dfs, ignore_index=True)
    print(f"BDL Game Outlook: {len(outlook)} games")
    
    # Extract dates from boxscores (they have a 'date' column)
    boxscores['date'] = pd.to_datetime(boxscores['date']).dt.date.astype(str)
    
    # Extract dates from outlook (from filename pattern or parse the date column)
    outlook['date_str'] = pd.to_datetime(outlook['date']).dt.date.astype(str)
    
    # Group by date and compare
    boxscore_by_date = boxscores.groupby('date').size()
    outlook_by_date = outlook.groupby('date_str').size()
    
    # Get all unique dates
    all_dates = sorted(set(boxscore_by_date.index) | set(outlook_by_date.index))
    
    print(f"\nDate-by-date comparison:")
    print(f"{'Date':<12} | {'Boxscores':>10} | {'Outlook':>10} | {'Diff':>6}")
    print("-" * 50)
    
    mismatches = []
    for date in all_dates:
        box_count = boxscore_by_date.get(date, 0)
        out_count = outlook_by_date.get(date, 0)
        diff = box_count - out_count
        
        status = "✅" if diff == 0 else "⚠️"
        print(f"{date:<12} | {box_count:>10} | {out_count:>10} | {diff:>+6} {status}")
        
        if diff != 0:
            mismatches.append((date, box_count, out_count, diff))
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"Total MLB Boxscores: {len(boxscores)}")
    print(f"Total BDL Game Outlook: {len(outlook)}")
    print(f"Difference: {len(boxscores) - len(outlook):+d}")
    
    if mismatches:
        print(f"\n⚠️ Found {len(mismatches)} date(s) with mismatches:")
        for date, box, out, diff in mismatches:
            print(f"  {date}: Boxscores={box}, Outlook={out} (diff={diff:+d})")
    else:
        print(f"\n✅ Perfect match! All dates have equal counts.")
    
    return len(boxscores) == len(outlook)

if __name__ == "__main__":
    compare_boxscores_and_outlook(2010)
