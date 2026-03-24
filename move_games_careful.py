"""
Carefully move games to correct dates, ensuring no games are lost.
"""

import pandas as pd
from pathlib import Path
import copy

# Team abbreviation mapping
ABBR_MAPPING = {
    'ARI': 'AZ',
    'CHW': 'CWS',
    'MIA': 'FLA',
}

print('=' * 80)
print('MOVING GAMES TO MATCH BOXSCORE DATES - CAREFUL VERSION')
print('=' * 80)

outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')

# Step 1: Load ALL outlook data into memory
print('\nStep 1: Loading all outlook files...')
all_outlook = {}
total_games_before = 0

for outlook_file in sorted(outlook_dir.glob('game_outlook_*.csv')):
    date = outlook_file.stem.split('_')[-1]
    df = pd.read_csv(outlook_file)
    all_outlook[date] = df.copy()
    total_games_before += len(df)

print(f'Loaded {len(all_outlook)} files with {total_games_before} total games')

# Step 2: Build a map of game_pk to current date location
print('\nStep 2: Mapping game_pk to current dates...')
game_pk_to_date = {}

for date, df in all_outlook.items():
    for _, row in df.iterrows():
        if pd.notna(row['game_pk']):
            pk = int(row['game_pk'])
            game_pk_to_date[pk] = date

print(f'Found {len(game_pk_to_date)} games with game_pk')

# Step 3: Determine which games need to move
print('\nStep 3: Determining which games need to move...')
moves_needed = {}  # {game_pk: (from_date, to_date, target_position)}

for boxscore_file in sorted(boxscore_dir.glob('boxscores_*.csv')):
    target_date = boxscore_file.stem.split('_')[-1]
    
    if target_date not in all_outlook:
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    outlook_df = all_outlook[target_date]
    
    outlook_pks = set(outlook_df['game_pk'].dropna().astype(int))
    
    # For each game in boxscore, check if it's in the correct outlook file
    for position, row in boxscore_df.iterrows():
        pk = row['game_pk']
        
        if pk not in outlook_pks:
            # This game should be in this date but isn't
            if pk in game_pk_to_date:
                current_date = game_pk_to_date[pk]
                if current_date != target_date:
                    moves_needed[pk] = (current_date, target_date, position)
                    print(f'  Game {pk}: {current_date} → {target_date} (position {position})')

print(f'\nTotal games to move: {len(moves_needed)}')

# Step 4: Execute moves
print('\nStep 4: Executing moves...')

for pk, (from_date, to_date, target_position) in moves_needed.items():
    # Extract the game row from source date
    from_df = all_outlook[from_date]
    game_row = from_df[from_df['game_pk'] == pk]
    
    if len(game_row) == 0:
        print(f'  ERROR: Game {pk} not found in {from_date}')
        continue
    
    game_row = game_row.iloc[0].copy()
    
    # Remove from source
    all_outlook[from_date] = from_df[from_df['game_pk'] != pk].copy()
    
    # Add to target at correct position
    to_df = all_outlook[to_date]
    
    # Create new df with game inserted at position
    game_df = pd.DataFrame([game_row])
    top = to_df.iloc[:target_position].copy()
    bottom = to_df.iloc[target_position:].copy()
    all_outlook[to_date] = pd.concat([top, game_df, bottom], ignore_index=True)

print(f'  Moved {len(moves_needed)} games')

# Step 5: Final sort by boxscore order for all dates
print('\nStep 5: Final sort by boxscore order...')

for date in all_outlook.keys():
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not boxscore_file.exists():
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    outlook_df = all_outlook[date]
    
    # Create ordering from boxscore
    boxscore_df['order'] = range(len(boxscore_df))
    pk_to_order = dict(zip(boxscore_df['game_pk'], boxscore_df['order']))
    
    # Apply to outlook (games not in boxscore go to end)
    outlook_df_copy = outlook_df.copy()
    outlook_df_copy['order'] = outlook_df_copy['game_pk'].map(pk_to_order)
    outlook_df_sorted = outlook_df_copy.sort_values('order', na_position='last')
    outlook_df_sorted = outlook_df_sorted.drop(columns=['order'])
    
    all_outlook[date] = outlook_df_sorted

# Step 6: Verify no games were lost
print('\nStep 6: Verification...')
total_games_after = sum(len(df) for df in all_outlook.values())

print(f'Games before: {total_games_before}')
print(f'Games after: {total_games_after}')

if total_games_before != total_games_after:
    print(f'  ⚠️  WARNING: Lost {total_games_before - total_games_after} games!')
else:
    print(f'  ✅ No games lost')

# Step 7: Save files
print('\nStep 7: Saving files...')

# Create backup
backup_dir = outlook_dir / 'backup_before_move_v2'
backup_dir.mkdir(exist_ok=True)

for outlook_file in outlook_dir.glob('game_outlook_*.csv'):
    backup_file = backup_dir / outlook_file.name
    import shutil
    shutil.copy(outlook_file, backup_file)

# Save all updated files
for date, df in all_outlook.items():
    outlook_file = outlook_dir / f'game_outlook_{date}.csv'
    df.to_csv(outlook_file, index=False)

print(f'  Saved {len(all_outlook)} files')
print(f'  Backup saved to: {backup_dir}/')

# Step 8: Final verification of alignment
print('\n' + '=' * 80)
print('ALIGNMENT VERIFICATION')
print('=' * 80)

perfect_dates = 0
total_dates = 0
total_positions_matched = 0
total_positions = 0

for date, outlook_df in all_outlook.items():
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not boxscore_file.exists():
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    
    outlook_pks = outlook_df['game_pk'].dropna().astype(int).tolist()
    boxscore_pks = boxscore_df['game_pk'].tolist()
    
    total_dates += 1
    
    # Check if counts match
    if len(outlook_pks) == len(boxscore_pks):
        # Check if order matches
        if all(outlook_pks[i] == boxscore_pks[i] for i in range(len(outlook_pks))):
            perfect_dates += 1
    
    # Count position matches
    for i in range(min(len(outlook_pks), len(boxscore_pks))):
        total_positions += 1
        if outlook_pks[i] == boxscore_pks[i]:
            total_positions_matched += 1

print(f'\nDates checked: {total_dates}')
print(f'Perfect dates: {perfect_dates} ({perfect_dates/total_dates*100:.1f}%)')
print(f'Position matches: {total_positions_matched}/{total_positions} ({total_positions_matched/total_positions*100:.1f}%)')

print(f'\n✅ Complete!')
