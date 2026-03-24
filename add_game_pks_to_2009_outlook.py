"""
Add MLB game_pk values to game outlook files and reorder to match boxscores.
"""

import pandas as pd
import glob
from pathlib import Path

# Team abbreviation mapping: balldontlie -> MLB historical
ABBR_MAPPING = {
    'ARI': 'AZ',
    'CHW': 'CWS',
    'MIA': 'FLA',
}

print('=' * 80)
print('ADDING GAME_PK TO 2009 GAME OUTLOOK FILES')
print('=' * 80)

outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')

outlook_files = sorted(outlook_dir.glob('game_outlook_*.csv'))

games_matched = 0
games_not_matched = 0
dates_processed = 0

# Create backup directory
backup_dir = outlook_dir / 'backup_before_game_pk'
backup_dir.mkdir(exist_ok=True)

print(f'\nProcessing {len(outlook_files)} dates...\n')

for outlook_file in outlook_files:
    date = outlook_file.stem.split('_')[-1]
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not boxscore_file.exists():
        print(f'⚠️  {date}: No boxscore file found, skipping')
        continue
    
    # Load data
    outlook_df = pd.read_csv(outlook_file)
    boxscore_df = pd.read_csv(boxscore_file)
    
    # Backup original file
    backup_file = backup_dir / outlook_file.name
    outlook_df.to_csv(backup_file, index=False)
    
    # Apply abbreviation mapping to outlook
    outlook_df['home_abbr_mapped'] = outlook_df['home_team_abbreviation'].map(
        lambda x: ABBR_MAPPING.get(x, x))
    outlook_df['away_abbr_mapped'] = outlook_df['away_team_abbreviation'].map(
        lambda x: ABBR_MAPPING.get(x, x))
    
    # Create matchup keys
    outlook_df['matchup'] = outlook_df['away_abbr_mapped'] + '@' + outlook_df['home_abbr_mapped']
    boxscore_df['matchup'] = boxscore_df['away_team_abbreviation'] + '@' + boxscore_df['home_team_abbreviation']
    
    # Create a mapping from matchup to game_pk
    matchup_to_pk = dict(zip(boxscore_df['matchup'], boxscore_df['game_pk']))
    
    # Add game_pk column to outlook
    outlook_df['game_pk'] = outlook_df['matchup'].map(matchup_to_pk)
    
    # Count matches
    matched = outlook_df['game_pk'].notna().sum()
    not_matched = outlook_df['game_pk'].isna().sum()
    games_matched += matched
    games_not_matched += not_matched
    
    # Reorder to match exact boxscore order (not just sorted by game_pk)
    # Create a mapping from game_pk to position in boxscore file
    boxscore_df['box_order'] = range(len(boxscore_df))
    pk_to_order = dict(zip(boxscore_df['game_pk'], boxscore_df['box_order']))
    
    # Add order column to outlook (NaN for unmatched games)
    outlook_df['box_order'] = outlook_df['game_pk'].map(pk_to_order)
    
    # Sort by boxscore order, putting unmatched games at the end
    outlook_df_sorted = outlook_df.sort_values('box_order', na_position='last')
    
    # Drop the temporary helper columns
    outlook_df_sorted = outlook_df_sorted.drop(columns=['home_abbr_mapped', 'away_abbr_mapped', 'matchup', 'box_order'])
    
    # Reorder columns to put game_pk first (after id)
    cols = outlook_df_sorted.columns.tolist()
    # Remove game_pk from its current position
    cols.remove('game_pk')
    # Insert it after 'id'
    id_idx = cols.index('id')
    cols.insert(id_idx + 1, 'game_pk')
    outlook_df_sorted = outlook_df_sorted[cols]
    
    # Save updated file
    outlook_df_sorted.to_csv(outlook_file, index=False)
    
    dates_processed += 1
    
    if not_matched > 0:
        print(f'⚠️  {date}: {matched} matched, {not_matched} not matched')
    elif dates_processed % 20 == 0:
        print(f'✓  Processed {dates_processed} dates...')

print(f'\n{"=" * 80}')
print(f'SUMMARY')
print(f'{"=" * 80}')
print(f'Dates processed:       {dates_processed}')
print(f'Games matched:         {games_matched}')
print(f'Games not matched:     {games_not_matched}')
print(f'Match rate:            {games_matched/(games_matched+games_not_matched)*100:.1f}%')

print(f'\n✅ Original files backed up to: {backup_dir}/')
print(f'✅ Game outlook files updated with game_pk column')
print(f'✅ Games reordered to match boxscore order')

# Verify a sample file
sample_date = '2009-04-06'
sample_file = outlook_dir / f'game_outlook_{sample_date}.csv'
if sample_file.exists():
    df = pd.read_csv(sample_file)
    print(f'\n{"=" * 80}')
    print(f'SAMPLE VERIFICATION: {sample_date}')
    print(f'{"=" * 80}')
    print(f'Columns: {", ".join(df.columns[:5])}...')
    print(f'First 3 game_pks: {df["game_pk"].head(3).tolist()}')
    print(f'Games with game_pk: {df["game_pk"].notna().sum()}')
    print(f'Games without game_pk: {df["game_pk"].isna().sum()}')
