import pandas as pd
import glob
import os
from collections import defaultdict

def filter_2010_by_game_pk():
    """
    Filter 2010 data by identifying duplicate game_pks (postponed games)
    and keeping only the actual played date for each game_pk.
    
    Similar approach to 2009, but using game_pk as the deduplication key.
    """
    
    print("="*80)
    print("FILTERING 2010: Deduplicating by game_pk")
    print("="*80)
    
    year = 2010
    base_path = f'data/{year}_data/mlb_data/raw'
    boxscore_path = f'{base_path}/boxscores'
    pitcher_path = f'{base_path}/starting_pitcher_boxscores'
    outlook_path = f'{base_path}/bdl_data/game_outlook'
    
    # Step 1: Backups already created by previous script
    print(f"\n  Step 1: Backups already created ✓")
    
    # Step 2: Load all boxscores and identify duplicates
    print(f"\n  Step 2: Loading boxscores and identifying duplicates...")
    
    boxscore_files = sorted(glob.glob(f'{boxscore_path}/boxscores_*.csv'))
    
    # Track all games by game_pk
    game_pk_dates = defaultdict(list)  # {game_pk: [(date, away, home), ...]}
    all_games = []  # [(date, game_pk, away, home, df_data), ...]
    
    for file in boxscore_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        
        for idx, row in df.iterrows():
            game_pk = int(row['game_pk'])
            away = row['away_team_abbreviation']
            home = row['home_team_abbreviation']
            
            game_pk_dates[game_pk].append((date, away, home))
            all_games.append((date, game_pk, away, home, row))
    
    print(f"    Total games loaded: {len(all_games)}")
    print(f"    Unique game_pks: {len(game_pk_dates)}")
    
    # Find duplicates
    duplicates = {pk: dates for pk, dates in game_pk_dates.items() if len(dates) > 1}
    print(f"    Duplicate game_pks: {len(duplicates)}")
    
    # Show some examples
    if duplicates:
        print(f"\n    Examples of duplicate game_pks:")
        for i, (game_pk, dates) in enumerate(list(duplicates.items())[:5]):
            print(f"      game_pk {game_pk}:")
            for date, away, home in dates:
                print(f"        {date}: {away} @ {home}")
    
    # Step 3: Determine which date to keep for each game_pk
    print(f"\n  Step 3: Determining correct date for each game...")
    
    # Strategy: Keep the LATER date (actual played date, not postponed date)
    game_pk_to_keep_date = {}
    
    for game_pk, dates in game_pk_dates.items():
        if len(dates) == 1:
            # Only one date, keep it
            game_pk_to_keep_date[game_pk] = dates[0][0]
        else:
            # Multiple dates, keep the latest one (actual played date)
            sorted_dates = sorted(dates, key=lambda x: x[0])
            game_pk_to_keep_date[game_pk] = sorted_dates[-1][0]
    
    games_to_keep = set()
    for date, game_pk, away, home, row_data in all_games:
        if game_pk_to_keep_date[game_pk] == date:
            games_to_keep.add((date, game_pk))
    
    print(f"    Games to keep: {len(games_to_keep)}")
    print(f"    Games to remove: {len(all_games) - len(games_to_keep)}")
    
    # Step 4: Filter boxscores
    print(f"\n  Step 4: Filtering boxscores...")
    
    box_before = 0
    box_after = 0
    
    for file in boxscore_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        box_before += len(df)
        
        df['_keep'] = df['game_pk'].apply(lambda pk: (date, int(pk)) in games_to_keep)
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
        
        df['_keep'] = df['game_pk'].apply(lambda pk: (date, int(pk)) in games_to_keep)
        df_filtered = df[df['_keep']].copy()
        if '_keep' in df_filtered.columns:
            df_filtered = df_filtered.drop('_keep', axis=1)
        df_filtered = df_filtered.reset_index(drop=True)
        pitch_after += len(df_filtered)
        
        df_filtered.to_csv(file, index=False)
    
    print(f"    Before: {pitch_before}, After: {pitch_after}, Removed: {pitch_before - pitch_after}")
    
    # Step 6: Rebuild game outlook to match boxscores
    print(f"\n  Step 6: Rebuilding game outlook to match boxscores...")
    
    outlook_files = sorted(glob.glob(f'{outlook_path}/game_outlook_*.csv'))
    
    outlook_before = 0
    outlook_after = 0
    
    # First, add game_pk to outlook files (if not present)
    for box_file in boxscore_files:
        date = box_file.split('_')[-1].replace('.csv', '')
        outlook_file = f'{outlook_path}/game_outlook_{date}.csv'
        
        if not os.path.exists(outlook_file):
            continue
        
        df_box = pd.read_csv(box_file)
        df_outlook = pd.read_csv(outlook_file)
        
        outlook_before += len(df_outlook)
        
        # Add game_pk if not present
        if 'game_pk' not in df_outlook.columns:
            # Match by (away, home) team
            game_pk_map = {}
            for _, row in df_box.iterrows():
                key = (row['away_team_abbreviation'], row['home_team_abbreviation'])
                game_pk_map[key] = row['game_pk']
            
            df_outlook['game_pk'] = df_outlook.apply(
                lambda row: game_pk_map.get(
                    (row['away_team_abbreviation'], row['home_team_abbreviation']),
                    None
                ),
                axis=1
            )
        
        # Filter to only games in boxscores
        df_outlook['_keep'] = df_outlook['game_pk'].apply(
            lambda pk: (date, int(pk)) in games_to_keep if pd.notna(pk) else False
        )
        df_outlook_filtered = df_outlook[df_outlook['_keep']].copy()
        if '_keep' in df_outlook_filtered.columns:
            df_outlook_filtered = df_outlook_filtered.drop('_keep', axis=1)
        df_outlook_filtered = df_outlook_filtered.reset_index(drop=True)
        outlook_after += len(df_outlook_filtered)
        
        df_outlook_filtered.to_csv(outlook_file, index=False)
    
    print(f"    Before: {outlook_before}, After: {outlook_after}, Removed: {outlook_before - outlook_after}")
    
    # Step 7: Verification
    print(f"\n  Step 7: Verification...")
    
    if box_after == pitch_after == outlook_after:
        print(f"    ✅ SUCCESS! All datasets: {box_after} games")
        
        # Check game_pk alignment
        perfect_alignment = 0
        total_files = 0
        
        for date in sorted(set([f.split('_')[-1].replace('.csv', '') for f in boxscore_files])):
            box_file = f'{boxscore_path}/boxscores_{date}.csv'
            pitch_file = f'{pitcher_path}/starting_pitcher_boxscores_{date}.csv'
            outlook_file = f'{outlook_path}/game_outlook_{date}.csv'
            
            if os.path.exists(box_file) and os.path.exists(pitch_file) and os.path.exists(outlook_file):
                df_box = pd.read_csv(box_file)
                df_pitch = pd.read_csv(pitch_file)
                df_outlook = pd.read_csv(outlook_file)
                
                if len(df_box) == len(df_pitch) == len(df_outlook):
                    box_pks = sorted(df_box['game_pk'].values)
                    pitch_pks = sorted(df_pitch['game_pk'].values)
                    outlook_pks = sorted(df_outlook['game_pk'].values)
                    
                    if (box_pks == pitch_pks) and (box_pks == outlook_pks):
                        perfect_alignment += 1
                
                total_files += 1
        
        print(f"    Perfect game_pk alignment: {perfect_alignment}/{total_files} dates ({100*perfect_alignment/total_files:.1f}%)")
        return True
    else:
        print(f"    ⚠️  Count mismatch:")
        print(f"      Boxscore: {box_after}")
        print(f"      Pitcher: {pitch_after}")
        print(f"      Outlook: {outlook_after}")
        return False

# Execute
success = filter_2010_by_game_pk()

print(f"\n{'='*80}")
if success:
    print("✅ 2010 SUCCESSFULLY DEDUPLICATED")
else:
    print("⚠️  2010 DEDUPLICATION COMPLETED WITH WARNINGS")
print('='*80)
