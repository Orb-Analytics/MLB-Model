import pandas as pd
import glob

def verify_file_by_file_alignment(year):
    """Verify that game_pk order matches between boxscores and outlook for each date."""
    
    print(f"\n{'='*80}")
    print(f"Verifying File-by-File game_pk Order Alignment for {year}")
    print('='*80)
    
    outlook_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
    
    all_match = True
    mismatches = []
    total_files = 0
    total_games = 0
    
    print(f"\nChecking {len(outlook_files)} date files...")
    
    for outlook_file in outlook_files:
        # Extract date from filename
        import os
        filename = os.path.basename(outlook_file)
        date_str = filename.replace('game_outlook_', '').replace('.csv', '')
        
        # Find corresponding boxscore file
        boxscore_file = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_{date_str}.csv'
        
        if not os.path.exists(boxscore_file):
            continue
        
        # Load both files
        outlook = pd.read_csv(outlook_file)
        boxscores = pd.read_csv(boxscore_file)
        
        # Get game_pk lists
        box_pks = boxscores['game_pk'].tolist()
        out_pks = outlook['game_pk'].tolist()
        
        total_files += 1
        total_games += len(box_pks)
        
        # Compare
        if box_pks != out_pks:
            all_match = False
            mismatches.append((date_str, box_pks, out_pks))
            print(f"\n  ❌ {date_str}:")
            print(f"      Boxscore order: {box_pks}")
            print(f"      Outlook order:  {out_pks}")
    
    print(f"\n{'='*80}")
    print("RESULTS")
    print('='*80)
    print(f"Files checked:       {total_files}")
    print(f"Games checked:       {total_games}")
    print(f"Files with matches:  {total_files - len(mismatches)}")
    print(f"Files with issues:   {len(mismatches)}")
    
    if all_match:
        print(f"\n✅ PERFECT ALIGNMENT!")
        print(f"   All {total_files} files have game_pks in identical order")
        return True
    else:
        print(f"\n❌ Found {len(mismatches)} file(s) with ordering issues")
        return False

if __name__ == "__main__":
    result = verify_file_by_file_alignment(2010)
    
    if result:
        print(f"\n{'='*80}")
        print("✅ VERIFICATION PASSED: All files aligned perfectly!")
        print('='*80)
    else:
        print(f"\n{'='*80}")
        print("❌ VERIFICATION FAILED: Some files have ordering issues")
        print('='*80)
