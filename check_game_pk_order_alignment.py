import pandas as pd
import glob

def check_game_pk_order_alignment(year):
    """Check if game_pks are in the exact same order in boxscores and pitcher files."""
    
    print(f"\n{'='*80}")
    print(f"Checking game_pk order alignment for {year}")
    print('='*80)
    
    # Load all boxscores
    boxscore_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv'))
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    
    # Load all starting pitcher boxscores
    pitcher_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/*.csv'))
    pitcher_dfs = [pd.read_csv(f) for f in pitcher_files]
    pitchers = pd.concat(pitcher_dfs, ignore_index=True)
    
    print(f"Boxscores: {len(boxscores)} records")
    print(f"Pitchers: {len(pitchers)} records")
    
    # Get game_pk lists
    boxscore_game_pks = boxscores['game_pk'].tolist()
    pitcher_game_pks = pitchers['game_pk'].tolist()
    
    # Check if lengths match
    if len(boxscore_game_pks) != len(pitcher_game_pks):
        print(f"❌ Length mismatch: {len(boxscore_game_pks)} vs {len(pitcher_game_pks)}")
        return False
    
    # Check if they're in the same order
    mismatches = []
    for i, (b_pk, p_pk) in enumerate(zip(boxscore_game_pks, pitcher_game_pks)):
        if b_pk != p_pk:
            mismatches.append((i, b_pk, p_pk))
    
    if mismatches:
        print(f"❌ Order mismatch: {len(mismatches)} differences found")
        print(f"\nFirst 10 mismatches:")
        for i, b_pk, p_pk in mismatches[:10]:
            print(f"  Row {i}: Boxscore={b_pk}, Pitcher={p_pk}")
        return False
    else:
        print(f"✅ Perfect alignment: All {len(boxscore_game_pks)} game_pks match in order")
        return True

if __name__ == "__main__":
    years = range(2010, 2025)
    
    results = {}
    for year in years:
        try:
            results[year] = check_game_pk_order_alignment(year)
        except Exception as e:
            print(f"❌ Error checking {year}: {str(e)}")
            results[year] = False
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    all_aligned = all(results.values())
    aligned_count = sum(results.values())
    
    print(f"\nYears with perfect alignment: {aligned_count}/{len(results)}")
    
    if all_aligned:
        print(f"\n✅ ALL YEARS PERFECTLY ALIGNED!")
        print("All game_pks are in the exact same order in boxscores and pitcher files.")
    else:
        print(f"\n⚠️ Years with misalignment:")
        for year, aligned in results.items():
            if not aligned:
                print(f"  {year}")
