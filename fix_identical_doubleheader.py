import pandas as pd
import os
from datetime import datetime as dt

def fix_identical_doubleheader(year):
    """Fix the BOS vs CHW Sept 4 doubleheader where both games have same score."""
    
    print(f"\n{'='*80}")
    print(f"Fixing Identical Score Doubleheader for {year}")
    print('='*80)
    
    # Create backup first
    backup_dir = f"data/{year}_data/mlb_data/raw/bdl_data/game_outlook_backup_{dt.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"\nCreating backup at: {backup_dir}")
    
    import glob, shutil
    outlook_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
    for f in outlook_files:
        shutil.copy2(f, backup_dir)
    
    # Load the Sept 4 file
    file_path = f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_2010-09-04.csv'
    df = pd.read_csv(file_path)
    
    print(f"\nBefore fix:")
    bos_chw = df[(df['home_team_abbreviation'] == 'BOS') & (df['away_team_abbreviation'] == 'CHW')]
    for _, g in bos_chw.iterrows():
        print(f"  BDL ID {g['id']}: game_pk = {int(g['game_pk'])}")
    
    # Assign BDL ID 46300 to game_pk 265814
    # Keep BDL ID 46310 with game_pk 265829
    df.loc[df['id'] == 46300, 'game_pk'] = 265814
    
    print(f"\nAfter fix:")
    bos_chw = df[(df['home_team_abbreviation'] == 'BOS') & (df['away_team_abbreviation'] == 'CHW')]
    for _, g in bos_chw.iterrows():
        print(f"  BDL ID {g['id']}: game_pk = {int(g['game_pk'])}")
    
    # Write back
    df.to_csv(file_path, index=False)
    
    print(f"\n✅ Fixed! Both games now have unique game_pks")
    print(f"Backup: {backup_dir}")

if __name__ == "__main__":
    fix_identical_doubleheader(2010)
