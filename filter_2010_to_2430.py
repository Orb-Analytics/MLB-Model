import pandas as pd
import glob
import os
import shutil
from collections import defaultdict

def process_2010():
    """
    Process 2010 data similar to 2009:
    1. Create backups
    2. Load original BDL games (from backup_original_2010)
    3. Match boxscores to BDL games
    4. Filter all three datasets to match BDL
    """
    
    print("="*80)
    print("PROCESSING 2010: Filtering to 2,430 games")
    print("="*80)
    
    year = 2010
    base_path = f'data/{year}_data/mlb_data/raw'
    outlook_path = f'{base_path}/bdl_data/game_outlook'
    boxscore_path = f'{base_path}/boxscores'
    pitcher_path = f'{base_path}/starting_pitcher_boxscores'
    
    # Team abbreviation mapping
    ABBR_MAPPING = {
        'ARI': 'AZ',
        'CHW': 'CWS',
        'MIA': 'FLA'  # 2010 is before the 2012 rebrand
    }
    
    def apply_abbr_mapping(team_abbr):
        if pd.isna(team_abbr):
            return team_abbr
        return ABBR_MAPPING.get(str(team_abbr).strip(), str(team_abbr).strip())
    
    # Step 1: Create backups
    print(f"\n  Step 1: Creating backups...")
    
    backup_box = f'{boxscore_path}/backup_before_filtering_2453'
    backup_pitch = f'{pitcher_path}/backup_before_filtering_2453'
    backup_outlook = f'{outlook_path}/backup_before_filtering_2453'
    
    if os.path.exists(backup_box):
        print(f"    ⚠️  Backup already exists at {backup_box}")
    else:
        os.makedirs(backup_box, exist_ok=True)
        os.system(f'cp {boxscore_path}/boxscores_*.csv {backup_box}/')
        print(f"    ✓ Created boxscore backup")
    
    if os.path.exists(backup_pitch):
        print(f"    ⚠️  Backup already exists at {backup_pitch}")
    else:
        os.makedirs(backup_pitch, exist_ok=True)
        os.system(f'cp {pitcher_path}/starting_pitcher_boxscores_*.csv {backup_pitch}/')
        print(f"    ✓ Created starting pitcher backup")
    
    if os.path.exists(backup_outlook):
        print(f"    ⚠️  Backup already exists at {backup_outlook}")
    else:
        os.makedirs(backup_outlook, exist_ok=True)
        os.system(f'cp {outlook_path}/game_outlook_*.csv {backup_outlook}/')
        print(f"    ✓ Created game outlook backup")
    
    # Step 2: Load original BDL games
    print(f"\n  Step 2: Loading original BDL games...")
    bdl_backup_path = f'{outlook_path}/backup_original_{year}'
    
    if not os.path.exists(bdl_backup_path):
        print(f"    ❌ No backup_original_{year} found!")
        return False
    
    bdl_games_by_date = {}  # {date: [(away, home), ...]}
    total_bdl = 0
    
    bdl_files = sorted(glob.glob(f'{bdl_backup_path}/game_outlook_*.csv'))
    for file in bdl_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        
        # Apply abbreviation mapping
        df['away_team_abbreviation'] = df['away_team_abbreviation'].apply(apply_abbr_mapping)
        df['home_team_abbreviation'] = df['home_team_abbreviation'].apply(apply_abbr_mapping)
        
        matchups = []
        for _, row in df.iterrows():
            away = row['away_team_abbreviation']
            home = row['home_team_abbreviation']
            matchups.append((away, home))
            total_bdl += 1
        
        bdl_games_by_date[date] = matchups
    
    print(f"    Original BDL: {total_bdl} games across {len(bdl_games_by_date)} dates")
    
    # Step 3: Match boxscore games to BDL
    print(f"\n  Step 3: Matching boxscore games to original BDL...")
    
    boxscore_files = sorted(glob.glob(f'{boxscore_path}/boxscores_*.csv'))
    
    games_to_keep = []  # (date, game_pk)
    games_to_remove = []
    
    for file in boxscore_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        
        bdl_matchups = bdl_games_by_date.get(date, [])
        bdl_matched = [False] * len(bdl_matchups)
        
        for _, row in df.iterrows():
            game_pk = int(row['game_pk'])
            away = row['away_team_abbreviation']
            home = row['home_team_abbreviation']
            matchup = (away, home)
            
            # Find this matchup in BDL games
            matched = False
            for i, bdl_matchup in enumerate(bdl_matchups):
                if bdl_matchup == matchup and not bdl_matched[i]:
                    bdl_matched[i] = True
                    matched = True
                    games_to_keep.append((date, game_pk))
                    break
            
            if not matched:
                games_to_remove.append((date, game_pk))
    
    print(f"    Games to keep: {len(games_to_keep)}")
    print(f"    Games to remove: {len(games_to_remove)}")
    
    if len(games_to_keep) != total_bdl:
        print(f"    ⚠️  Warning: Expected {total_bdl} games to keep, got {len(games_to_keep)}")
    
    # Step 4: Filter boxscores
    print(f"\n  Step 4: Filtering boxscores...")
    keep_set = set(games_to_keep)
    
    box_before = 0
    box_after = 0
    
    for file in boxscore_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        box_before += len(df)
        
        df['_keep'] = df['game_pk'].apply(lambda pk: (date, int(pk)) in keep_set)
        df_filtered = df[df['_keep']].copy()
        if '_keep' in df_filtered.columns:
            df_filtered = df_filtered.drop('_keep', axis=1)
        df_filtered = df_filtered.reset_index(drop=True)
        box_after += len(df_filtered)
        
        df_filtered.to_csv(file, index=False)
    
    print(f"    Before: {box_before}, After: {box_after}, Removed: {box_before - box_after}")
    
    # Step 5: Filter starting pitcher boxscores
    print(f"\n  Step 5: Filtering starting pitcher boxscores...")
    pitcher_files = sorted(glob.glob(f'{pitcher_path}/starting_pitcher_boxscores_*.csv'))
    
    pitch_before = 0
    pitch_after = 0
    
    for file in pitcher_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        pitch_before += len(df)
        
        df['_keep'] = df['game_pk'].apply(lambda pk: (date, int(pk)) in keep_set)
        df_filtered = df[df['_keep']].copy()
        if '_keep' in df_filtered.columns:
            df_filtered = df_filtered.drop('_keep', axis=1)
        df_filtered = df_filtered.reset_index(drop=True)
        pitch_after += len(df_filtered)
        
        df_filtered.to_csv(file, index=False)
    
    print(f"    Before: {pitch_before}, After: {pitch_after}, Removed: {pitch_before - pitch_after}")
    
    # Step 6: Verify
    print(f"\n  Step 6: Verification...")
    
    if box_after == pitch_after == total_bdl:
        print(f"    ✅ SUCCESS! All datasets: {box_after} games (matches original BDL count)")
        
        # Check alignment
        perfect_dates = 0
        total_dates = 0
        
        for date in sorted(bdl_games_by_date.keys()):
            box_file = f'{boxscore_path}/boxscores_{date}.csv'
            pitch_file = f'{pitcher_path}/starting_pitcher_boxscores_{date}.csv'
            
            if os.path.exists(box_file) and os.path.exists(pitch_file):
                df_box = pd.read_csv(box_file)
                df_pitch = pd.read_csv(pitch_file)
                
                if len(df_box) == len(bdl_games_by_date[date]):
                    if (df_box['game_pk'].values == df_pitch['game_pk'].values).all():
                        perfect_dates += 1
                
                total_dates += 1
        
        print(f"    Perfect date alignment: {perfect_dates}/{total_dates} dates ({100*perfect_dates/total_dates:.1f}%)")
        return True
    else:
        print(f"    ⚠️  Count mismatch:")
        print(f"      Boxscore: {box_after}")
        print(f"      Pitcher: {pitch_after}")
        print(f"      Original BDL: {total_bdl}")
        return False

# Execute
success = process_2010()

print(f"\n{'='*80}")
if success:
    print("✅ 2010 SUCCESSFULLY FILTERED TO 2,430 GAMES")
else:
    print("⚠️  2010 FILTERING COMPLETED WITH WARNINGS")
print('='*80)
