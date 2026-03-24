import pandas as pd
import glob
import os

def verify_outlook_pitcher_alignment(year):
    """Verify that game_pk order matches between outlook and starting pitcher files."""
    
    print(f"\n{'='*80}")
    print(f"Verifying Game Outlook vs Starting Pitcher Alignment for {year}")
    print('='*80)
    
    outlook_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
    
    all_match = True
    mismatches = []
    total_files = 0
    total_games = 0
    
    print(f"\nChecking {len(outlook_files)} date files...")
    
    for outlook_file in outlook_files:
        # Extract date from filename
        filename = os.path.basename(outlook_file)
        date_str = filename.replace('game_outlook_', '').replace('.csv', '')
        
        # Find corresponding starting pitcher file
        pitcher_file = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date_str}.csv'
        
        if not os.path.exists(pitcher_file):
            continue
        
        # Load both files
        outlook = pd.read_csv(outlook_file)
        pitchers = pd.read_csv(pitcher_file)
        
        # Get game_pk lists
        pitch_pks = pitchers['game_pk'].tolist()
        out_pks = outlook['game_pk'].tolist()
        
        total_files += 1
        total_games += len(pitch_pks)
        
        # Compare
        if pitch_pks != out_pks:
            all_match = False
            mismatches.append(date_str)
            if len(mismatches) <= 5:  # Show first 5 mismatches
                print(f"\n  ❌ {date_str}:")
                print(f"      Pitcher order: {pitch_pks[:10]}{'...' if len(pitch_pks) > 10 else ''}")
                print(f"      Outlook order: {out_pks[:10]}{'...' if len(out_pks) > 10 else ''}")
    
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
        print(f"\n⚠️  Found {len(mismatches)} file(s) with ordering differences")
        if len(mismatches) > 5:
            print(f"    (showing first 5, {len(mismatches) - 5} more not shown)")
        return False

if __name__ == "__main__":
    result = verify_outlook_pitcher_alignment(2010)
    
    if result:
        print(f"\n{'='*80}")
        print("✅ VERIFICATION PASSED: Outlook and Pitcher files aligned!")
        print('='*80)
    else:
        print(f"\n{'='*80}")
        print("⚠️  VERIFICATION: Order differences detected")
        print("   Reordering may be needed")
        print('='*80)
