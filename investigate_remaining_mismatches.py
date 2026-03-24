"""
Investigate remaining mismatches after the move.
"""

import pandas as pd
from pathlib import Path

print('=' * 80)
print('INVESTIGATING REMAINING MISMATCHES')
print('=' * 80)

outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')

dates_with_issues = []

for outlook_file in sorted(outlook_dir.glob('game_outlook_*.csv')):
    date = outlook_file.stem.split('_')[-1]
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not boxscore_file.exists():
        continue
    
    outlook_df = pd.read_csv(outlook_file)
    boxscore_df = pd.read_csv(boxscore_file)
    
    outlook_pks = outlook_df['game_pk'].dropna().astype(int).tolist()
    boxscore_pks = boxscore_df['game_pk'].tolist()
    
    # Check if perfect match
    is_perfect = (len(outlook_pks) == len(boxscore_pks) and 
                  all(outlook_pks[i] == boxscore_pks[i] for i in range(len(outlook_pks))))
    
    if not is_perfect:
        outlook_set = set(outlook_pks)
        boxscore_set = set(boxscore_pks)
        
        missing_from_outlook = boxscore_set - outlook_set
        missing_from_boxscore = outlook_set - boxscore_set
        
        dates_with_issues.append({
            'date': date,
            'outlook_count': len(outlook_pks),
            'boxscore_count': len(boxscore_pks),
            'missing_from_outlook': missing_from_outlook,
            'missing_from_boxscore': missing_from_boxscore,
            'outlook_pks': outlook_pks[:5],
            'boxscore_pks': boxscore_pks[:5]
        })

print(f'\nFound {len(dates_with_issues)} dates with issues\n')

# Show first 10 problem dates
for issue in dates_with_issues[:10]:
    print(f'{issue["date"]}:')
    print(f'  Outlook: {issue["outlook_count"]} games')
    print(f'  Boxscore: {issue["boxscore_count"]} games')
    
    if issue['missing_from_outlook']:
        print(f'  Missing from outlook: {sorted(issue["missing_from_outlook"])}')
    if issue['missing_from_boxscore']:
        print(f'  Missing from boxscore: {sorted(issue["missing_from_boxscore"])}')
    
    # Check if order is the only issue
    if not issue['missing_from_outlook'] and not issue['missing_from_boxscore']:
        print(f'  Issue: Same games, wrong order')
        print(f'    Outlook order:  {issue["outlook_pks"]}')
        print(f'    Boxscore order: {issue["boxscore_pks"]}')
    print()

if len(dates_with_issues) > 10:
    print(f'... and {len(dates_with_issues) - 10} more dates with issues\n')

# Check for games that still need to be moved
print('=' * 80)
print('GAMES THAT STILL NEED TO BE MOVED')
print('=' * 80)

all_needed_moves = []

for issue in dates_with_issues:
    if issue['missing_from_outlook']:
        for pk in issue['missing_from_outlook']:
            # Find where this game currently is
            for outlook_file in outlook_dir.glob('game_outlook_*.csv'):
                search_date = outlook_file.stem.split('_')[-1]
                df = pd.read_csv(outlook_file)
                if pk in df['game_pk'].values:
                    all_needed_moves.append((pk, search_date, issue['date']))
                    break

print(f'\nTotal games still needing to move: {len(all_needed_moves)}')

if all_needed_moves:
    print('\nGames to move:')
    for pk, current, target in all_needed_moves[:20]:
        print(f'  Game {pk}: {current} → {target}')
    if len(all_needed_moves) > 20:
        print(f'  ... and {len(all_needed_moves) - 20} more')

# Summary
print(f'\n{"=" * 80}')
print('SUMMARY')
print(f'{"=" * 80}')
print(f'Total dates: {len(list(outlook_dir.glob("game_outlook_*.csv")))}')
print(f'Dates with issues: {len(dates_with_issues)}')
print(f'Dates perfect: {len(list(outlook_dir.glob("game_outlook_*.csv"))) - len(dates_with_issues)}')
print(f'Games still need moving: {len(all_needed_moves)}')
