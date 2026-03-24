import pandas as pd
import glob
import os

def verify_all_three_datasets_alignment(year):
    """Verify that game_pk order matches across boxscores, pitchers, and outlook."""
    
    print(f"\n{'='*80}")
    print(f"Verifying 3-Way Alignment: Boxscores, Pitchers, Outlook for {year}")
    print('='*80)
    
    outlook_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
    
    all_match = True
    total_files = 0
    total_games = 0
    
    print(f"\nChecking {len(outlook_files)} date files...")
    
    sample_dates = []
    
    for outlook_file in outlook_files:
        # Extract date from filename
        filename = os.path.basename(outlook_file)
        date_str = filename.replace('game_outlook_', '').replace('.csv', '')
        
        # Find corresponding files
        boxscore_file = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_{date_str}.csv'
        pitcher_file = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date_str}.csv'
        
        if not os.path.exists(boxscore_file) or not os.path.exists(pitcher_file):
            continue
        
        # Load all three files
        outlook = pd.read_csv(outlook_file)
        boxscores = pd.read_csv(boxscore_file)
        pitchers = pd.read_csv(pitcher_file)
        
        # Get game_pk lists
        box_pks = boxscores['game_pk'].tolist()
        pitch_pks = pitchers['game_pk'].tolist()
        out_pks = outlook['game_pk'].tolist()
        
        total_files += 1
        total_games += len(box_pks)
        
        # Check if all three match
        if box_pks == pitch_pks == out_pks:
            # Store sample for display
            if len(sample_dates) < 3:
                sample_dates.append((date_str, box_pks, pitch_pks, out_pks))
        else:
            all_match = False
            print(f"\n  ❌ {date_str}:")
            if box_pks != pitch_pks:
                print(f"      Boxscore ≠ Pitcher")
            if box_pks != out_pks:
                print(f"      Boxscore ≠ Outlook")
            if pitch_pks != out_pks:
                print(f"      Pitcher ≠ Outlook")
    
    print(f"\n{'='*80}")
    print("RESULTS")
    print('='*80)
    print(f"Files checked:       {total_files}")
    print(f"Games checked:       {total_games}")
    
    if all_match:
        print(f"\n✅ PERFECT 3-WAY ALIGNMENT!")
        print(f"   All {total_files} files have identical game_pk order across:")
        print(f"   • Boxscores")
        print(f"   • Starting Pitcher Boxscores")
        print(f"   • Game Outlook")
        
        print(f"\n{'='*80}")
        print("Sample Verification (First 3 dates):")
        print('='*80)
        for date_str, box_pks, pitch_pks, out_pks in sample_dates:
            print(f"\n{date_str} ({len(box_pks)} games):")
            print(f"  Boxscores: {box_pks[:5]}{'...' if len(box_pks) > 5 else ''}")
            print(f"  Pitchers:  {pitch_pks[:5]}{'...' if len(pitch_pks) > 5 else ''}")
            print(f"  Outlook:   {out_pks[:5]}{'...' if len(out_pks) > 5 else ''}")
            print(f"  ✅ All match!")
        
        return True
    else:
        print(f"\n❌ ALIGNMENT ISSUES FOUND")
        return False

if __name__ == "__main__":
    result = verify_all_three_datasets_alignment(2010)
    
    if result:
        print(f"\n{'='*80}")
        print("✅ ALL THREE DATASETS PERFECTLY ALIGNED!")
        print("   Can merge by game_pk or by position within each date")
        print('='*80)
