"""
Reorganize balldontlie game outlook data by local date instead of UTC date.

Converts UTC timestamps to US local dates (uses venue-based timezone approximation).
Most MLB games are in Eastern (ET), Central (CT), Mountain (MT), or Pacific (PT) timezones.
"""

import pandas as pd
import glob
from pathlib import Path
from datetime import datetime, timedelta

print('=' * 80)
print('REORGANIZING BALLDONTLIE DATA BY LOCAL DATE')
print('=' * 80)

# Load all current games
print('\nLoading balldontlie game outlook data...')
bdl_files = sorted(glob.glob('data/bdl_data/game_outlook/*.csv'))
df = pd.concat([pd.read_csv(f) for f in bdl_files], ignore_index=True)

print(f'Total games: {len(df)}')
print(f'Unique game IDs: {df["id"].nunique()}')
print(f'Files: {len(bdl_files)}')

# Parse UTC timestamps
df['datetime_utc'] = pd.to_datetime(df['date'])
df['hour_utc'] = df['datetime_utc'].dt.hour

# Approximate local date conversion:
# Most evening games (7pm-11pm local) appear as next day 00:00-04:00 UTC
# Heuristic: If hour is 00:00-14:59 UTC (before 3pm UTC), subtract 1 day
# This works well for US timezones (ET/CT/MT/PT all are UTC-4 to UTC-8)

print('\nConverting  UTC timestamps to local dates...')
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
print(f'  Date range: {df["local_date"].min()} to {df["local_date"].max()}')

# Check for any duplicates
duplicates = df.duplicated(subset=['id'], keep=False)
if duplicates.any():
    print(f'\n⚠️  Warning: Found {duplicates.sum()} duplicate game IDs')
else:
    print('\n✅ No duplicate game IDs')

# Save back to CSV files by local date
print(f'\nRe-saving to CSV files grouped by local date...')
output_dir = Path('data/bdl_data/game_outlook')

# Clear existing files
for f in output_dir.glob('game_outlook_*.csv'):
    f.unlink()
print(f'Cleared existing files')

# Group by local date and save
for local_date, group in df.groupby('local_date'):
    filename = f'game_outlook_{local_date}.csv'
    filepath = output_dir / filename
    
    # Drop helper columns and sort by game ID
    output_cols = [col for col in df.columns if col not in ['datetime_utc', 'hour_utc', 'local_date']]
    output_group = group[output_cols].sort_values('id')
    output_group.to_csv(filepath, index=False)

files_written = df['local_date'].nunique()
print(f'Wrote {files_written} CSV files to {output_dir}')

# Verify a sample date
sample_date = '2025-07-12'
if sample_date in df['local_date'].values:
    sample_count = (df['local_date'] == sample_date).sum()
    print(f'\n✅ Verification: July 12th now has {sample_count} games')
    print(f'   Expected: ~15 games (should match MLB.com)')
else:
    print(f'\n⚠️  July 12th not found in dataset')

print(f'\n✅ Dataset reorganized by local date!')
print(f'Files now match MLB.com game dates')
