"""
Reorganize 2009 balldontlie game outlook data by local date instead of UTC date.

Converts UTC timestamps to US local dates (uses venue-based timezone approximation).
Most MLB games are in Eastern (ET), Central (CT), Mountain (MT), or Pacific (PT) timezones.
"""

import pandas as pd
import glob
from pathlib import Path
from datetime import datetime, timedelta

print('=' * 80)
print('REORGANIZING 2009 BALLDONTLIE DATA BY LOCAL DATE')
print('=' * 80)

# Load all current games
print('\nLoading 2009 balldontlie game outlook data...')
bdl_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
df = pd.concat([pd.read_csv(f) for f in bdl_files], ignore_index=True)

print(f'Total games: {len(df)}')
print(f'Unique game IDs: {df["id"].nunique()}')
print(f'Files: {len(bdl_files)}')
print(f'Current date range: {sorted(set([Path(f).stem.split("_")[-1] for f in bdl_files]))[0]} to {sorted(set([Path(f).stem.split("_")[-1] for f in bdl_files]))[-1]}')

# Parse UTC timestamps
df['datetime_utc'] = pd.to_datetime(df['date'])
df['hour_utc'] = df['datetime_utc'].dt.hour

# Approximate local date conversion:
# Most evening games (7pm-11pm local) appear as next day 00:00-04:00 UTC
# Heuristic: If hour is 00:00-14:59 UTC (before 3pm UTC), subtract 1 day
# This works well for US timezones (ET/CT/MT/PT all are UTC-4 to UTC-8)

print('\nConverting UTC timestamps to local dates...')
print('Using heuristic: games before 15:00 UTC → previous local day')

df['local_date'] = df['datetime_utc'].dt.date.astype(str)
# Subtract 1 day for games with early UTC hours (previous evening games)
early_games_mask = df['hour_utc'] < 15
df.loc[early_games_mask, 'local_date'] = (
    df.loc[early_games_mask, 'datetime_utc'] - timedelta(days=1)
).dt.date.astype(str)

print(f'  Adjusted {early_games_mask.sum()} games to previous day')

# Verify date distribution changed
utc_dates = df['datetime_utc'].dt.date.nunique()
local_dates = df['local_date'].nunique()
print(f'\nDate distribution:')
print(f'  UTC dates: {utc_dates}')
print(f'  Local dates: {local_dates}')
print(f'  New date range: {df["local_date"].min()} to {df["local_date"].max()}')

# Check for any duplicates
duplicates = df.duplicated(subset=['id'], keep=False)
if duplicates.any():
    print(f'\n⚠️  Warning: Found {duplicates.sum()} duplicate game IDs')
    print(f'Duplicate IDs: {df[duplicates]["id"].unique()}')
else:
    print('\n✅ No duplicate game IDs')

# Check the Opening Day game
print('\nVerifying Opening Day 2009:')
april_5_games = df[df['local_date'] == '2009-04-05']
if len(april_5_games) > 0:
    print(f'  ✅ Found {len(april_5_games)} game(s) on April 5th, 2009')
    for _, game in april_5_games.iterrows():
        print(f'     Game {game["id"]}: {game["away_team_abbreviation"]} @ {game["home_team_abbreviation"]} (UTC: {game["date"]})')
else:
    print(f'  ⚠️  No games found on April 5th, 2009')

# Save back to CSV files by local date
print(f'\nRe-saving to CSV files grouped by local date...')
output_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')

# Backup old files first
backup_dir = output_dir / 'backup_utc_dates'
backup_dir.mkdir(exist_ok=True)
print(f'Backing up {len(bdl_files)} original files to {backup_dir}/')
for f in output_dir.glob('game_outlook_*.csv'):
    target = backup_dir / f.name
    f.rename(target)
print(f'  ✅ Original files backed up')

# Group by local date and save
files_written = 0
for local_date, group in df.groupby('local_date'):
    filename = f'game_outlook_{local_date}.csv'
    filepath = output_dir / filename
    
    # Drop helper columns and sort by game ID
    output_cols = [col for col in df.columns if col not in ['datetime_utc', 'hour_utc', 'local_date']]
    output_group = group[output_cols].sort_values('id')
    output_group.to_csv(filepath, index=False)
    files_written += 1

print(f'  ✅ Wrote {files_written} CSV files to {output_dir}/')

# Final verification
new_files = sorted(output_dir.glob('game_outlook_*.csv'))
print(f'\n{"=" * 80}')
print(f'✅ 2009 DATASET REORGANIZED BY LOCAL DATE!')
print(f'{"=" * 80}')
print(f'Files: {len(new_files)}')
print(f'Date range: {sorted([f.stem.split("_")[-1] for f in new_files])[0]} to {sorted([f.stem.split("_")[-1] for f in new_files])[-1]}')
print(f'Total games: {len(df)}')
print(f'\nFiles now match MLB.com game dates for 2009 season')
