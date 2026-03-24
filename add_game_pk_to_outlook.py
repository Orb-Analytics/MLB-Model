import pandas as pd
import glob
import os
from datetime import datetime as dt

def add_game_pk_to_outlook(year):
    """Add game_pk column to game outlook files by matching with boxscores."""
    
    # Team abbreviation mapping: Outlook → Boxscore format
    TEAM_MAPPING = {
        'ARI': 'AZ',   # Arizona Diamondbacks
        'CHW': 'CWS',  # Chicago White Sox
        'MIA': 'FLA',  # Miami/Florida Marlins
    }
    
    print(f"\n{'='*80}")
    print(f"Adding game_pk to Game Outlook for {year}")
    print('='*80)
    
    # Create backup first
    backup_dir = f"data/{year}_data/mlb_data/raw/bdl_data/game_outlook_backup_{dt.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"\nCreating backup at: {backup_dir}")
    
    outlook_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
    import shutil
    for f in outlook_files:
        shutil.copy2(f, backup_dir)
    
    # Load all boxscores to create a lookup
    print(f"\nLoading boxscores...")
    boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    
    # Parse date
    boxscores['date'] = pd.to_datetime(boxscores['date']).dt.date.astype(str)
    
    # Create lookup key: date + home_team + away_team + scores (for doubleheaders)
    boxscores['lookup_key'] = (boxscores['date'] + '_' + 
                                boxscores['home_team_abbreviation'] + '_' + 
                                boxscores['away_team_abbreviation'] + '_' +
                                boxscores['home_batting_r'].astype(str) + '_' +
                                boxscores['away_batting_r'].astype(str))
    
    # Create game_pk lookup dictionary
    game_pk_lookup = dict(zip(boxscores['lookup_key'], boxscores['game_pk']))
    
    print(f"Loaded {len(boxscores)} boxscores")
    print(f"Created lookup with {len(game_pk_lookup)} keys")
    
    # Process each outlook file
    total_files = len(outlook_files)
    matched = 0
    unmatched = 0
    
    print(f"\nProcessing {total_files} game outlook files...")
    
    for i, outlook_file in enumerate(outlook_files, 1):
        # Load outlook file
        outlook = pd.read_csv(outlook_file)
        
        # Parse date from outlook
        outlook['date_parsed'] = pd.to_datetime(outlook['date']).dt.date.astype(str)
        
        # Map team abbreviations to boxscore format
        outlook['home_team_mapped'] = outlook['home_team_abbreviation'].replace(TEAM_MAPPING)
        outlook['away_team_mapped'] = outlook['away_team_abbreviation'].replace(TEAM_MAPPING)
        
        # Create lookup key for outlook using mapped abbreviations AND scores
        outlook['lookup_key'] = (outlook['date_parsed'] + '_' + 
                                  outlook['home_team_mapped'] + '_' + 
                                  outlook['away_team_mapped'] + '_' +
                                  outlook['home_team_score'].astype(str) + '_' +
                                  outlook['away_team_score'].astype(str))
        
        # Map game_pk
        outlook['game_pk'] = outlook['lookup_key'].map(game_pk_lookup)
        
        # Count matches
        file_matched = outlook['game_pk'].notna().sum()
        file_unmatched = outlook['game_pk'].isna().sum()
        matched += file_matched
        unmatched += file_unmatched
        
        if file_unmatched > 0:
            print(f"\n  ⚠️  File {i}/{total_files}: {os.path.basename(outlook_file)}")
            print(f"      Matched: {file_matched}, Unmatched: {file_unmatched}")
            # Show unmatched games
            unmatched_games = outlook[outlook['game_pk'].isna()][['home_team_abbreviation', 'away_team_abbreviation', 'date_parsed']]
            for _, row in unmatched_games.iterrows():
                print(f"        {row['home_team_abbreviation']} vs {row['away_team_abbreviation']} on {row['date_parsed']}")
        
        # Drop helper columns
        outlook = outlook.drop(['date_parsed', 'lookup_key', 'home_team_mapped', 'away_team_mapped'], axis=1)
        
        # Reorder columns to make game_pk first
        cols = ['game_pk'] + [col for col in outlook.columns if col != 'game_pk']
        outlook = outlook[cols]
        
        # Write back
        outlook.to_csv(outlook_file, index=False)
        
        if (i % 20 == 0) or (i == total_files):
            print(f"  Processed {i}/{total_files} files...")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"Total games in outlook: {matched + unmatched}")
    print(f"Successfully matched: {matched}")
    print(f"Unmatched: {unmatched}")
    print(f"Match rate: {100 * matched / (matched + unmatched):.2f}%")
    print(f"\nBackup: {backup_dir}")
    
    if unmatched > 0:
        print(f"\n⚠️  Warning: {unmatched} games could not be matched to boxscores")
    else:
        print(f"\n✅ All games successfully matched!")

if __name__ == "__main__":
    add_game_pk_to_outlook(2010)
