import pandas as pd
import glob
import os
import shutil

def find_and_restore_missing_pitcher_records(year):
    """Find missing pitcher records and restore them from backup."""
    
    print(f"\n{'='*80}")
    print(f"Processing {year}")
    print('='*80)
    
    # Load current boxscores
    boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    boxscore_game_pks = set(boxscores['game_pk'].unique())
    print(f"Total boxscore records: {len(boxscores)}")
    print(f"Unique game_pks in boxscores: {len(boxscore_game_pks)}")
    
    # Load current pitcher records
    pitcher_files = glob.glob(f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/*.csv')
    pitcher_dfs = [pd.read_csv(f) for f in pitcher_files]
    pitchers = pd.concat(pitcher_dfs, ignore_index=True)
    pitcher_game_pks = set(pitchers['game_pk'].unique())
    print(f"Total pitcher records: {len(pitchers)}")
    print(f"Unique game_pks in pitchers: {len(pitcher_game_pks)}")
    
    # Find missing game_pks
    missing_game_pks = boxscore_game_pks - pitcher_game_pks
    
    if not missing_game_pks:
        print(f"✅ No missing pitcher records for {year}")
        return 0
    
    print(f"\n⚠️ Missing {len(missing_game_pks)} pitcher record(s): {sorted(missing_game_pks)}")
    
    # Find backup directory
    backup_dirs = glob.glob(f'data/{year}_data/mlb_data/raw/backup_before_deduplication_*')
    if not backup_dirs:
        print(f"❌ No backup directory found for {year}")
        return 0
    
    backup_dir = sorted(backup_dirs)[-1]  # Use most recent backup
    print(f"\nFound backup: {os.path.basename(backup_dir)}")
    
    # Load pitcher records from backup
    backup_pitcher_files = glob.glob(f'{backup_dir}/starting_pitcher_boxscores/*.csv')
    if not backup_pitcher_files:
        print(f"❌ No pitcher backup files found")
        return 0
    
    backup_pitcher_dfs = [pd.read_csv(f) for f in backup_pitcher_files]
    backup_pitchers = pd.concat(backup_pitcher_dfs, ignore_index=True)
    print(f"Backup pitcher records: {len(backup_pitchers)}")
    
    # Find the missing records in backup
    missing_records = backup_pitchers[backup_pitchers['game_pk'].isin(missing_game_pks)].copy()
    
    if len(missing_records) == 0:
        print(f"❌ Missing records not found in backup")
        return 0
    
    print(f"\n✅ Found {len(missing_records)} missing record(s) in backup:")
    for _, record in missing_records.iterrows():
        game_info = boxscores[boxscores['game_pk'] == record['game_pk']].iloc[0]
        print(f"  game_pk {record['game_pk']}: {game_info['date']} - {record['pitcher_name']}")
    
    # Group by date and add to current files
    for date, group in missing_records.groupby('date'):
        output_file = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date}.csv'
        
        if os.path.exists(output_file):
            # Append to existing file
            existing = pd.read_csv(output_file)
            combined = pd.concat([existing, group], ignore_index=True)
            combined = combined.drop_duplicates(subset=['game_pk'], keep='last')
            combined.to_csv(output_file, index=False)
            print(f"\n✅ Added {len(group)} record(s) to {os.path.basename(output_file)}")
        else:
            # Create new file
            group.to_csv(output_file, index=False)
            print(f"\n✅ Created {os.path.basename(output_file)} with {len(group)} record(s)")
    
    return len(missing_records)

if __name__ == "__main__":
    years_to_check = [2016, 2018, 2019, 2020]
    
    total_restored = 0
    for year in years_to_check:
        restored = find_and_restore_missing_pitcher_records(year)
        total_restored += restored
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: Restored {total_restored} pitcher record(s) total")
    print('='*80)
