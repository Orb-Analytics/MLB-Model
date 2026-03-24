import pandas as pd
import glob
import os
from collections import defaultdict

def filter_year_to_match_bdl(year):
    """Filter year to remove duplicate game_pks, keeping only games from original BDL"""
    
    print("="*80)
    print(f"FILTERING YEAR {year}")
    print("="*80)
    
    base_path = f'data/{year}_data/mlb_data/raw'
    outlook_path = f'{base_path}/bdl_data/game_outlook'
    boxscore_path = f'{base_path}/boxscores'
    pitcher_path = f'{base_path}/starting_pitcher_boxscores'
    
    # Team abbreviation mapping
    ABBR_MAPPING = {'ARI': 'AZ', 'CHW': 'CWS'}
    if year < 2012:
        ABBR_MAPPING['MIA'] = 'FLA'
    
    def apply_abbr_mapping(team_abbr):
        if pd.isna(team_abbr):
            return team_abbr
        return ABBR_MAPPING.get(str(team_abbr).strip(), str(team_abbr).strip())
    
    # Load original BDL games from backup
    print(f"\n  Step 1: Loading original BDL games from backup...")
    backup_files = sorted(glob.glob(f'{outlook_path}/backup_original_{year}/game_outlook_*.csv'))
    
    if not backup_files:
        print(f"    ⚠️  No backup found")
        return False
    
    bdl_games_by_date = {}
    total_bdl = 0
    
    for file in backup_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        df['away_team_abbreviation'] = df['away_team_abbreviation'].apply(apply_abbr_mapping)
        df['home_team_abbreviation'] = df['home_team_abbreviation'].apply(apply_abbr_mapping)
        
        date_matchups = []
        for _, row in df.iterrows():
            away = row['away_team_abbreviation']
            home = row['home_team_abbreviation']
            date_matchups.append((away, home))
            total_bdl += 1
        
        bdl_games_by_date[date] = date_matchups
    
    print(f"    Original BDL: {total_bdl} games across {len(bdl_games_by_date)} dates")
    
    # Load boxscore games and match to BDL
    print(f"\n  Step 2: Matching boxscore games to original BDL...")
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
    
    #Create backup before filtering
    print(f"\n  Step 3: Creating backup before filtering...")
    backup_unfiltered = f'{outlook_path}/backup_unfiltered_{year}'
    os.makedirs(backup_unfiltered, exist_ok=True)
    os.system(f'cp {outlook_path}/game_outlook_*.csv {backup_unfiltered}/ 2>/dev/null')
    
    backup_box = f'{boxscore_path}/backup_unfiltered_{year}'
    os.makedirs(backup_box, exist_ok=True)
    os.system(f'cp {boxscore_path}/boxscores_*.csv {backup_box}/ 2>/dev/null')
    
    backup_pitch = f'{pitcher_path}/backup_unfiltered_{year}'
    os.makedirs(backup_pitch, exist_ok=True)
    os.system(f'cp {pitcher_path}/starting_pitcher_boxscores_*.csv {backup_pitch}/ 2>/dev/null')
    print(f"    ✓ Backups created")
    
    # Convert to set for filtering
    keep_set = set(games_to_keep)
    
    # Filter boxscores
    print(f"\n  Step 4: Filtering boxscores...")
    box_before = 0
    box_after = 0
    
    for file in boxscore_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        box_before += len(df)
        
        df['_keep'] = df['game_pk'].apply(lambda pk: (date, pk) in keep_set)
        df_filtered = df[df['_keep']].drop('_keep', axis=1).reset_index(drop=True)
        box_after += len(df_filtered)
        
        df_filtered.to_csv(file, index=False)
    
    print(f"    Before: {box_before}, After: {box_after}, Removed: {box_before - box_after}")
    
    # Filter starting pitcher boxscores
    print(f"\n  Step 5: Filtering starting pitcher boxscores...")
    pitcher_files = sorted(glob.glob(f'{pitcher_path}/starting_pitcher_boxscores_*.csv'))
    pitch_before = 0
    pitch_after = 0
    
    for file in pitcher_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        pitch_before += len(df)
        
        df['_keep'] = df['game_pk'].apply(lambda pk: (date, pk) in keep_set)
        df_filtered = df[df['_keep']].drop('_keep', axis=1).reset_index(drop=True)
        pitch_after += len(df_filtered)
        
        df_filtered.to_csv(file, index=False)
    
    print(f"    Before: {pitch_before}, After: {pitch_after}, Removed: {pitch_before - pitch_after}")
    
    # Filter game outlook
    print(f"\n  Step 6: Filtering game outlook...")
    outlook_files = sorted(glob.glob(f'{outlook_path}/game_outlook_*.csv'))
    out_before = 0
    out_after = 0
    
    for file in outlook_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        out_before += len(df)
        
        df['_keep'] = df['game_pk'].apply(lambda pk: (date, pk) in keep_set)
        df_filtered = df[df['_keep']].drop('_keep', axis=1).reset_index(drop=True)
        out_after += len(df_filtered)
        
        df_filtered.to_csv(file, index=False)
    
    print(f"    Before: {out_before}, After: {out_after}, Removed: {out_before - out_after}")
    
    # Verify
    print(f"\n  Step 7: Verification...")
    if box_after == pitch_after == out_after == total_bdl:
        print(f"    ✅ SUCCESS! All datasets: {box_after} games (matches original BDL count)")
        return True
    else:
        print(f"    ⚠️  Count mismatch:")
        print(f"      Boxscore: {box_after}")
        print(f"      Pitcher: {pitch_after}")
        print(f"      Outlook: {out_after}")
        print(f"      Original BDL: {total_bdl}")
        return False

# Process all years
print("\n" + "="*80)
print("FILTERING YEARS 2010-2024 TO MATCH ORIGINAL BDL DATA")
print("="*80 + "\n")

years = range(2010, 2025)
results = {}

for year in years:
    success = filter_year_to_match_bdl(year)
    results[year] = success
    print()

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

successful = [y for y, s in results.items() if s]
failed = [y for y, s in results.items() if not s]

print(f"\nSuccessful: {len(successful)} years")
for year in successful:
    print(f"  ✓ {year}")

if failed:
    print(f"\nFailed: {len(failed)} years")
    for year in failed:
        print(f"  ✗ {year}")

print("="*80)
