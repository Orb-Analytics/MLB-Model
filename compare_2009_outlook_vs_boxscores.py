"""
Compare 2009 game outlook files with boxscore files to verify game counts match by date.
"""

import pandas as pd
import glob
from pathlib import Path
from collections import defaultdict

print('=' * 80)
print('COMPARING 2009 GAME OUTLOOK VS BOXSCORE FILES')
print('=' * 80)

# Load game outlook files
print('\nLoading game outlook files...')
outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
outlook_files = sorted(outlook_dir.glob('game_outlook_*.csv'))
outlook_counts = {}
outlook_total = 0

for f in outlook_files:
    date = f.stem.split('_')[-1]  # Extract date from filename
    df = pd.read_csv(f)
    count = len(df)
    outlook_counts[date] = count
    outlook_total += count

print(f'  Found {len(outlook_files)} game outlook files')
print(f'  Total games: {outlook_total}')
print(f'  Date range: {min(outlook_counts.keys())} to {max(outlook_counts.keys())}')

# Load boxscore files
print('\nLoading boxscore files...')
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')
boxscore_files = sorted(boxscore_dir.glob('boxscores_*.csv'))
boxscore_counts = {}
boxscore_total = 0

for f in boxscore_files:
    date = f.stem.split('_')[-1]  # Extract date from filename
    df = pd.read_csv(f)
    # Each boxscore row is one complete game with both teams' stats
    count = len(df)
    boxscore_counts[date] = count
    boxscore_total += count

print(f'  Found {len(boxscore_files)} boxscore files')
print(f'  Total games: {boxscore_total}')
print(f'  Date range: {min(boxscore_counts.keys())} to {max(boxscore_counts.keys())}')

# Compare dates
print('\n' + '=' * 80)
print('COMPARISON RESULTS')
print('=' * 80)

all_dates = sorted(set(outlook_counts.keys()) | set(boxscore_counts.keys()))

mismatches = []
outlook_only = []
boxscore_only = []

for date in all_dates:
    outlook_count = outlook_counts.get(date, 0)
    boxscore_count = boxscore_counts.get(date, 0)
    
    if outlook_count == 0:
        boxscore_only.append((date, boxscore_count))
    elif boxscore_count == 0:
        outlook_only.append((date, outlook_count))
    elif outlook_count != boxscore_count:
        mismatches.append((date, outlook_count, boxscore_count))

# Report results
if not mismatches and not outlook_only and not boxscore_only:
    print('\n✅ PERFECT MATCH!')
    print(f'All {len(all_dates)} dates have matching game counts')
    print(f'Total: {outlook_total} games in both datasets')
else:
    if mismatches:
        print(f'\n⚠️  MISMATCHES FOUND: {len(mismatches)} dates with different counts')
        print('\nDate          | Outlook | Boxscore | Difference')
        print('-' * 50)
        for date, outlook_count, boxscore_count in mismatches[:20]:
            diff = outlook_count - boxscore_count
            print(f'{date} | {outlook_count:7} | {boxscore_count:8} | {diff:+10}')
        if len(mismatches) > 20:
            print(f'... and {len(mismatches) - 20} more mismatches')
    
    if outlook_only:
        print(f'\n⚠️  OUTLOOK ONLY: {len(outlook_only)} dates in outlook but not boxscore')
        for date, count in outlook_only[:10]:
            print(f'  {date}: {count} games')
        if len(outlook_only) > 10:
            print(f'  ... and {len(outlook_only) - 10} more dates')
    
    if boxscore_only:
        print(f'\n⚠️  BOXSCORE ONLY: {len(boxscore_only)} dates in boxscore but not outlook')
        for date, count in boxscore_only[:10]:
            print(f'  {date}: {count} games')
        if len(boxscore_only) > 10:
            print(f'  ... and {len(boxscore_only) - 10} more dates')

# Summary statistics
print('\n' + '=' * 80)
print('SUMMARY')
print('=' * 80)
print(f'Total dates in outlook:  {len(outlook_counts)}')
print(f'Total dates in boxscore: {len(boxscore_counts)}')
print(f'Total games in outlook:  {outlook_total}')
print(f'Total games in boxscore: {boxscore_total}')
print(f'Game difference:         {outlook_total - boxscore_total:+}')

# Check specific dates mentioned in the problem
print('\n' + '=' * 80)
print('OPENING DAY VERIFICATION')
print('=' * 80)
april_5 = '2009-04-05'
print(f'\nApril 5, 2009 (Opening Day):')
print(f'  Game outlook: {outlook_counts.get(april_5, 0)} game(s)')
print(f'  Boxscore:     {boxscore_counts.get(april_5, 0)} game(s)')
if outlook_counts.get(april_5, 0) == boxscore_counts.get(april_5, 0) == 1:
    print(f'  ✅ Match! Both have 1 game (Braves @ Phillies)')
else:
    print(f'  ⚠️  Mismatch or missing data')
