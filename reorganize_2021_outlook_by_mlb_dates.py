import pandas as pd
import glob
import os
from datetime import datetime

# Team abbreviation mapping
abbr_map = {
    'AZ': 'ARI',
    'ARI': 'ARI',
    'CWS': 'CHW',
    'CHW': 'CHW',
    'FLA': 'MIA',
    'MIA': 'MIA',
}

def normalize_abbr(abbr):
    """Normalize team abbreviations"""
    return abbr_map.get(abbr, abbr)

print("="*70)
print("STEP 1: Creating backup of 2021 BDL game outlook files")
print("="*70)

# Create backup
backup_dir = f'data/2021_data/mlb_data/raw/bdl_data/game_outlook_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
os.makedirs(backup_dir, exist_ok=True)

outlook_files = sorted(glob.glob('data/2021_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
for file in outlook_files:
    import shutil
    shutil.copy2(file, backup_dir)

print(f"Backed up {len(outlook_files)} files to {backup_dir}")

print("\n" + "="*70)
print("STEP 2: Loading MLB boxscores")
print("="*70)

# Read all MLB boxscores with date info
boxscore_files = sorted(glob.glob('data/2021_data/mlb_data/raw/boxscores/*.csv'))
all_boxscores = []

for file in boxscore_files:
    df = pd.read_csv(file)
    date_str = os.path.basename(file).replace('boxscores_', '').replace('.csv', '')
    df['mlb_date'] = date_str
    all_boxscores.append(df)

boxscores_df = pd.concat(all_boxscores, ignore_index=True)
print(f"Total MLB boxscores: {len(boxscores_df)}")

# Normalize team abbreviations
boxscores_df['away_team_abbrev_norm'] = boxscores_df['away_team_abbreviation'].apply(normalize_abbr)
boxscores_df['home_team_abbrev_norm'] = boxscores_df['home_team_abbreviation'].apply(normalize_abbr)

# Create match key
boxscores_df['match_key'] = (
    boxscores_df['away_team_abbrev_norm'] + '|' +
    boxscores_df['home_team_abbrev_norm'] + '|' +
    boxscores_df['away_batting_r'].astype(str) + '-' +
    boxscores_df['home_batting_r'].astype(str)
)

# Create lookup: match_key -> (game_pk, mlb_date)
match_to_game = {}
for _, row in boxscores_df.iterrows():
    key = row['match_key']
    game_pk = row['game_pk']
    mlb_date = row['mlb_date']
    
    if key not in match_to_game:
        match_to_game[key] = []
    match_to_game[key].append((game_pk, mlb_date))

print(f"Created lookup with {len(match_to_game)} unique match keys")

# Create game_pk -> MLB date mapping for reordering
game_pk_to_mlb_date = {row['game_pk']: row['mlb_date'] for _, row in boxscores_df.iterrows()}
game_pk_order_by_date = {}
for _, row in boxscores_df.iterrows():
    mlb_date = row['mlb_date']
    if mlb_date not in game_pk_order_by_date:
        game_pk_order_by_date[mlb_date] = []
    game_pk_order_by_date[mlb_date].append(row['game_pk'])

print("\n" + "="*70)
print("STEP 3: Loading all BDL game outlook data")
print("="*70)

# Read ALL outlook files into one dataframe
all_outlook = []
for file in outlook_files:
    df = pd.read_csv(file)
    all_outlook.append(df)

outlook_df = pd.concat(all_outlook, ignore_index=True)
print(f"Total BDL outlook games: {len(outlook_df)}")

print("\n" + "="*70)
print("STEP 4: Adding game_pk and MLB date to outlook")
print("="*70)

# Normalize team abbreviations
outlook_df['away_abbr_norm'] = outlook_df['away_team_abbreviation'].apply(normalize_abbr)
outlook_df['home_abbr_norm'] = outlook_df['home_team_abbreviation'].apply(normalize_abbr)

# Create match key
outlook_df['match_key'] = (
    outlook_df['away_abbr_norm'] + '|' +
    outlook_df['home_abbr_norm'] + '|' +
    outlook_df['away_team_score'].astype(str) + '-' +
    outlook_df['home_team_score'].astype(str)
)

# Track used game_pks for doubleheaders
used_pks = {}
matched = 0
unmatched = 0

game_pks = []
mlb_dates = []

for idx, row in outlook_df.iterrows():
    key = row['match_key']
    
    if key in match_to_game:
        available = match_to_game[key]
        
        if len(available) == 1:
            # Single match
            game_pk, mlb_date = available[0]
            game_pks.append(game_pk)
            mlb_dates.append(mlb_date)
            matched += 1
        else:
            # Doubleheader - find unused game_pk
            used_for_key = used_pks.get(key, [])
            
            pk_to_use = None
            date_to_use = None
            for game_pk, mlb_date in available:
                if game_pk not in used_for_key:
                    pk_to_use = game_pk
                    date_to_use = mlb_date
                    break
            
            if pk_to_use is None:
                # Shouldn't happen, but use first
                pk_to_use, date_to_use = available[0]
            
            game_pks.append(pk_to_use)
            mlb_dates.append(date_to_use)
            
            if key not in used_pks:
                used_pks[key] = []
            used_pks[key].append(pk_to_use)
            matched += 1
    else:
        game_pks.append(None)
        mlb_dates.append(None)
        unmatched += 1

outlook_df['game_pk'] = game_pks
outlook_df['mlb_date'] = mlb_dates

print(f"Matched: {matched} ({matched/len(outlook_df)*100:.2f}%)")
print(f"Unmatched: {unmatched}")

# Drop temporary columns
outlook_df = outlook_df.drop(['away_abbr_norm', 'home_abbr_norm', 'match_key'], axis=1)

# Reorder columns to put game_pk as second column
cols = outlook_df.columns.tolist()
cols.remove('game_pk')
cols.remove('mlb_date')
cols.insert(1, 'game_pk')
# mlb_date is just for reorganizing, we'll drop it later

print("\n" + "="*70)
print("STEP 5: Reorganizing files by MLB date")
print("="*70)

# First, remove all existing outlook files
for file in outlook_files:
    os.remove(file)
print(f"Removed {len(outlook_files)} old outlook files")

# Group by mlb_date and write new files
files_created = 0
total_games_written = 0

for mlb_date, group_df in outlook_df.groupby('mlb_date'):
    if pd.isna(mlb_date):
        print(f"  WARNING: Skipping {len(group_df)} games with no MLB date")
        continue
    
    # Get the order from boxscores
    if mlb_date in game_pk_order_by_date:
        boxscore_order = game_pk_order_by_date[mlb_date]
        
        # Create a dict for easy lookup
        game_dict = {row['game_pk']: row for _, row in group_df.iterrows()}
        
        # Reorder according to boxscore
        ordered_rows = []
        for game_pk in boxscore_order:
            if game_pk in game_dict:
                ordered_rows.append(game_dict[game_pk])
        
        if len(ordered_rows) > 0:
            ordered_df = pd.DataFrame(ordered_rows)
            # Drop mlb_date column
            ordered_df = ordered_df.drop('mlb_date', axis=1)
            
            # Write to file
            outlook_file = f'data/2021_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{mlb_date}.csv'
            ordered_df.to_csv(outlook_file, index=False)
            
            files_created += 1
            total_games_written += len(ordered_df)

print(f"Created {files_created} new outlook files")
print(f"Total games written: {total_games_written}")

print("\n" + "="*70)
print("STEP 6: Verifying alignment")
print("="*70)

# Verify alignment
verification_count = 0
aligned_count = 0

for boxscore_file in boxscore_files[:10]:
    date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
    outlook_file = f'data/2021_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date_str}.csv'
    
    if not os.path.exists(outlook_file):
        print(f"  ✗ {date_str}: outlook file missing")
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    outlook_df = pd.read_csv(outlook_file)
    
    boxscore_pks = boxscore_df['game_pk'].tolist()
    outlook_pks = outlook_df['game_pk'].tolist()
    
    verification_count += 1
    if boxscore_pks == outlook_pks:
        print(f"  ✓ {date_str}: {len(boxscore_pks)} games perfectly aligned")
        aligned_count += 1
    else:
        print(f"  ✗ {date_str}: {len(boxscore_pks)} boxscore vs {len(outlook_pks)} outlook")

print(f"\nAlignment: {aligned_count}/{verification_count} files")

# Final count
final_outlook_files = glob.glob('data/2021_data/mlb_data/raw/bdl_data/game_outlook/*.csv')
final_count = sum(len(pd.read_csv(f)) for f in final_outlook_files)
boxscore_count = len(boxscores_df)

print(f"\n{'='*70}")
print(f"Final outlook game count: {final_count}")
print(f"MLB boxscore count: {boxscore_count}")
print(f"Difference: {boxscore_count - final_count}")
print(f"Files: {len(final_outlook_files)} outlook vs {len(boxscore_files)} boxscore")
print("="*70)
