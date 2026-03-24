import pandas as pd
import glob
import os
from datetime import datetime as dt

def reorder_outlook_to_match_boxscores(year):
    """Reorder games within each outlook file to match boxscore game_pk order."""
    
    print(f"\n{'='*80}")
    print(f"Reordering Game Outlook Files to Match Boxscores for {year}")
    print('='*80)
    
    # Create backup first
    backup_dir = f"data/{year}_data/mlb_data/raw/bdl_data/game_outlook_backup_{dt.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"\nCreating backup at: {backup_dir}")
    
    outlook_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
    import shutil
    for f in outlook_files:
        shutil.copy2(f, backup_dir)
    
    print(f"\nProcessing {len(outlook_files)} files...")
    
    files_reordered = 0
    files_already_ordered = 0
    total_games_checked = 0
    
    for outlook_file in outlook_files:
        # Extract date from filename
        filename = os.path.basename(outlook_file)
        date_str = filename.replace('game_outlook_', '').replace('.csv', '')
        
        # Find corresponding boxscore file
        boxscore_file = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_{date_str}.csv'
        
        if not os.path.exists(boxscore_file):
            print(f"  ⚠️  No matching boxscore for {filename}")
            continue
        
        # Load both files
        outlook = pd.read_csv(outlook_file)
        boxscores = pd.read_csv(boxscore_file)
        
        # Get game_pk order from boxscore
        boxscore_order = boxscores['game_pk'].tolist()
        
        # Get current outlook order
        outlook_order = outlook['game_pk'].tolist()
        
        total_games_checked += len(outlook)
        
        # Check if already in correct order
        if outlook_order == boxscore_order:
            files_already_ordered += 1
            continue
        
        # Need to reorder
        files_reordered += 1
        
        # Create a mapping of game_pk to position in boxscore
        position_map = {pk: i for i, pk in enumerate(boxscore_order)}
        
        # Add sort key to outlook based on boxscore position
        outlook['_sort_key'] = outlook['game_pk'].map(position_map)
        
        # Check for any games that don't have a match
        unmatched = outlook[outlook['_sort_key'].isna()]
        if len(unmatched) > 0:
            print(f"\n  ⚠️  {filename} has {len(unmatched)} games not in boxscore:")
            for _, g in unmatched.iterrows():
                print(f"      game_pk {int(g['game_pk'])}: {g['home_team_abbreviation']} vs {g['away_team_abbreviation']}")
        
        # Sort by the boxscore order
        outlook_sorted = outlook.sort_values('_sort_key').drop('_sort_key', axis=1)
        
        # Verify the order now matches
        new_order = outlook_sorted['game_pk'].tolist()
        if new_order != boxscore_order:
            print(f"\n  ❌ {filename}: Reorder failed!")
            print(f"      Expected order: {boxscore_order}")
            print(f"      Got order:      {new_order}")
            continue
        
        # Write back
        outlook_sorted.to_csv(outlook_file, index=False)
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"Files processed:        {len(outlook_files)}")
    print(f"Files reordered:        {files_reordered}")
    print(f"Files already ordered:  {files_already_ordered}")
    print(f"Total games checked:    {total_games_checked}")
    print(f"\nBackup: {backup_dir}")
    
    if files_reordered > 0:
        print(f"\n✅ Reordered {files_reordered} file(s) to match boxscore order")
    else:
        print(f"\n✅ All files were already in correct order!")

if __name__ == "__main__":
    reorder_outlook_to_match_boxscores(2010)
