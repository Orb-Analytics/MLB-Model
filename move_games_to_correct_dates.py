"""
Move misplaced games to their correct date files and positions to match boxscore files.
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

# Team abbreviation mapping
ABBR_MAPPING = {
    'ARI': 'AZ',
    'CHW': 'CWS',
    'MIA': 'FLA',
}

print('=' * 80)
print('MOVING MISPLACED GAMES TO CORRECT DATE FILES')
print('=' * 80)

outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')

# Step 1: Find all games that need to be moved
print('\nStep 1: Identifying misplaced games...')

games_to_move = []  # (game_pk, current_date, target_date)
games_missing_from_outlook = {}  # {target_date: [(game_pk, boxscore_position)]}

for boxscore_file in sorted(boxscore_dir.glob('boxscores_*.csv')):
    date = boxscore_file.stem.split('_')[-1]
    outlook_file = outlook_dir / f'game_outlook_{date}.csv'
    
    if not outlook_file.exists():
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    outlook_df = pd.read_csv(outlook_file)
    
    boxscore_pks = set(boxscore_df['game_pk'].tolist())
    outlook_pks = set(outlook_df['game_pk'].dropna().astype(int).tolist())
    
    # Find games in boxscore but not in this date's outlook
    missing = boxscore_pks - outlook_pks
    if missing:
        if date not in games_missing_from_outlook:
            games_missing_from_outlook[date] = []
        
        for pk in missing:
            box_position = boxscore_df[boxscore_df['game_pk'] == pk].index[0]
            games_missing_from_outlook[date].append((pk, box_position))

print(f'Found {sum(len(v) for v in games_missing_from_outlook.values())} games missing from their target dates')

# Step 2: Find where these games currently are in outlook
print('\nStep 2: Locating games in current outlook files...')

game_pk_to_current_date = {}  # {game_pk: date}

for outlook_file in sorted(outlook_dir.glob('game_outlook_*.csv')):
    date = outlook_file.stem.split('_')[-1]
    outlook_df = pd.read_csv(outlook_file)
    
    for _, row in outlook_df.iterrows():
        if pd.notna(row['game_pk']):
            pk = int(row['game_pk'])
            game_pk_to_current_date[pk] = date

# Match up games that need to be moved
for target_date, missing_games in games_missing_from_outlook.items():
    for pk, box_position in missing_games:
        if pk in game_pk_to_current_date:
            current_date = game_pk_to_current_date[pk]
            if current_date != target_date:
                games_to_move.append((pk, current_date, target_date, box_position))
                print(f'  Game {pk}: {current_date} → {target_date} (position {box_position})')

print(f'\nTotal games to move: {len(games_to_move)}')

# Step 3: Load all outlook files, remove games from wrong dates, add to correct dates
print('\nStep 3: Removing games from wrong dates...')

all_outlook_data = {}  # {date: dataframe}

for outlook_file in sorted(outlook_dir.glob('game_outlook_*.csv')):
    date = outlook_file.stem.split('_')[-1]
    all_outlook_data[date] = pd.read_csv(outlook_file)

games_to_remove = defaultdict(set)  # {date: set of game_pks to remove}
games_to_add = defaultdict(list)  # {date: list of (position, game_row)}

for pk, current_date, target_date, box_position in games_to_move:
    games_to_remove[current_date].add(pk)
    
    # Get the game row from current date
    current_df = all_outlook_data[current_date]
    game_row = current_df[current_df['game_pk'] == pk].iloc[0]
    games_to_add[target_date].append((box_position, game_row))

# Remove games from their wrong dates
for date, pks_to_remove in games_to_remove.items():
    df = all_outlook_data[date]
    all_outlook_data[date] = df[~df['game_pk'].isin(pks_to_remove)]
    print(f'  Removed {len(pks_to_remove)} games from {date}')

# Step 4: Add games to correct dates at correct positions
print('\nStep 4: Adding games to correct dates...')

for date, games in games_to_add.items():
    df = all_outlook_data[date]
    
    # Sort games by their target position
    games.sort(key=lambda x: x[0])
    
    # Insert each game at the correct position
    for position, game_row in games:
        # Convert Series to DataFrame with single row
        game_df = pd.DataFrame([game_row])
        
        # Insert at the correct position
        top = df.iloc[:position]
        bottom = df.iloc[position:]
        df = pd.concat([top, game_df, bottom], ignore_index=True)
    
    all_outlook_data[date] = df
    print(f'  Added {len(games)} games to {date}')

# Step 5: Re-sort all files by boxscore order to ensure perfect alignment
print('\nStep 5: Re-sorting all files by boxscore order...')

for date, outlook_df in all_outlook_data.items():
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not boxscore_file.exists():
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    
    # Create order mapping from boxscore
    boxscore_df['box_order'] = range(len(boxscore_df))
    pk_to_order = dict(zip(boxscore_df['game_pk'], boxscore_df['box_order']))
    
    # Apply to outlook
    outlook_df['box_order'] = outlook_df['game_pk'].map(pk_to_order)
    outlook_df = outlook_df.sort_values('box_order', na_position='last')
    outlook_df = outlook_df.drop(columns=['box_order'])
    
    all_outlook_data[date] = outlook_df

# Step 6: Save all updated outlook files
print('\nStep 6: Saving updated files...')

# Create backup
backup_dir = outlook_dir / 'backup_before_move'
backup_dir.mkdir(exist_ok=True)

for outlook_file in outlook_dir.glob('game_outlook_*.csv'):
    backup_file = backup_dir / outlook_file.name
    outlook_file.rename(backup_file)

files_saved = 0
for date, df in all_outlook_data.items():
    outlook_file = outlook_dir / f'game_outlook_{date}.csv'
    df.to_csv(outlook_file, index=False)
    files_saved += 1

print(f'  Saved {files_saved} updated files')
print(f'  Original files backed up to: {backup_dir}/')

# Step 7: Verify the results
print('\n' + '=' * 80)
print('VERIFICATION')
print('=' * 80)

total_matches = 0
total_positions = 0
dates_perfect = 0
dates_checked = 0

for outlook_file in sorted(outlook_dir.glob('game_outlook_*.csv')):
    date = outlook_file.stem.split('_')[-1]
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not boxscore_file.exists():
        continue
    
    outlook_df = pd.read_csv(outlook_file)
    boxscore_df = pd.read_csv(boxscore_file)
    
    outlook_pks = outlook_df['game_pk'].dropna().astype(int).tolist()
    boxscore_pks = boxscore_df['game_pk'].tolist()
    
    # Check position matches
    matches = 0
    for i in range(len(outlook_pks)):
        total_positions += 1
        if i < len(boxscore_pks) and outlook_pks[i] == boxscore_pks[i]:
            matches += 1
            total_matches += 1
    
    dates_checked += 1
    if matches == len(outlook_pks) and len(outlook_pks) == len(boxscore_pks):
        dates_perfect += 1

print(f'\nDates checked: {dates_checked}')
print(f'Dates with perfect match: {dates_perfect} ({dates_perfect/dates_checked*100:.1f}%)')
print(f'Total positions: {total_positions}')
print(f'Matching positions: {total_matches} ({total_matches/total_positions*100:.1f}%)')

print(f'\n✅ Games moved to correct date files and positions!')
