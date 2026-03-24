import pandas as pd
import glob
import os
from datetime import datetime as dt

def fix_mismatched_games(year):
    """Fix specific games that are on wrong dates in game outlook."""
    
    print(f"\n{'='*80}")
    print(f"Fixing Date Mismatches for {year}")
    print('='*80)
    
    # Games to move: (game_id, from_date, to_date, matchup)
    moves = [
        (3726, '2010-04-16', '2010-04-17', 'BOS vs TB'),
        (16382, '2010-05-25', '2010-05-26', 'MIN vs NYY'),
    ]
    
    # Create backup first
    backup_dir = f"data/{year}_data/mlb_data/raw/bdl_data/game_outlook_backup_{dt.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"\nCreating backup at: {backup_dir}")
    
    outlook_files = glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv')
    import shutil
    for f in outlook_files:
        shutil.copy2(f, backup_dir)
    
    # Process each move
    for game_id, from_date, to_date, matchup in moves:
        print(f"\nMoving game {game_id} ({matchup}): {from_date} → {to_date}")
        
        # Load the source file
        from_file = f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{from_date}.csv'
        from_df = pd.read_csv(from_file)
        
        # Find the game to move
        game_to_move = from_df[from_df['id'] == game_id]
        
        if len(game_to_move) == 0:
            print(f"  ⚠️  Game {game_id} not found in {from_date} file")
            continue
        
        if len(game_to_move) > 1:
            print(f"  ⚠️  Multiple games with ID {game_id} found")
            continue
        
        print(f"  Found: {game_to_move.iloc[0]['home_team_abbreviation']} vs {game_to_move.iloc[0]['away_team_abbreviation']}")
        
        # Update the date in the game record
        game_to_move = game_to_move.copy()
        game_to_move['date'] = to_date + 'T00:00:00.000Z'
        
        # Remove from source file
        from_df_updated = from_df[from_df['id'] != game_id]
        
        # Load the destination file
        to_file = f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{to_date}.csv'
        
        if os.path.exists(to_file):
            to_df = pd.read_csv(to_file)
            # Add the game
            to_df_updated = pd.concat([to_df, game_to_move], ignore_index=True)
        else:
            # Create new file with just this game
            to_df_updated = game_to_move
        
        # Write both files
        from_df_updated.to_csv(from_file, index=False)
        to_df_updated.to_csv(to_file, index=False)
        
        print(f"  ✅ Moved successfully")
        print(f"     {from_date}: {len(from_df)} → {len(from_df_updated)} games")
        print(f"     {to_date}: {len(pd.read_csv(to_file)) - len(game_to_move)} → {len(to_df_updated)} games")
    
    print(f"\n{'='*80}")
    print("Fix Complete!")
    print('='*80)
    print(f"Backup: {backup_dir}")

if __name__ == "__main__":
    fix_mismatched_games(2010)
