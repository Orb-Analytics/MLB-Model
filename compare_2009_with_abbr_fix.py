"""
Re-compare 2009 outlook vs boxscores after fixing team abbreviation mismatches.
"""

import pandas as pd
import glob
from pathlib import Path

# Team abbreviation mapping: balldontlie -> MLB historical
ABBR_MAPPING = {
    'ARI': 'AZ',   # Arizona Diamondbacks
    'CHW': 'CWS',  # Chicago White Sox
    'MIA': 'FLA',  # Florida Marlins (2009)
}

print('=' * 80)
print('2009 COMPARISON WITH TEAM ABBREVIATION CORRECTIONS')
print('=' * 80)

# Load all game outlook files
outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
outlook_files = sorted(outlook_dir.glob('game_outlook_*.csv'))

# Load all boxscore files
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')
boxscore_files = sorted(boxscore_dir.glob('boxscores_*.csv'))

all_boxscore_only = []
all_outlook_only = []
date_mismatches = []

total_matched = 0
total_outlook_games = 0
total_boxscore_games = 0

print(f'\nApplying abbreviation mappings: {ABBR_MAPPING}')
print(f'Processing {len(outlook_files)} dates...\n')

for outlook_file in outlook_files:
    date = outlook_file.stem.split('_')[-1]
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not boxscore_file.exists():
        continue
    
    outlook_df = pd.read_csv(outlook_file)
    boxscore_df = pd.read_csv(boxscore_file)
    
    # Apply abbreviation mapping to outlook data
    outlook_df['home_abbr_mapped'] = outlook_df['home_team_abbreviation'].map(
        lambda x: ABBR_MAPPING.get(x, x))
    outlook_df['away_abbr_mapped'] = outlook_df['away_team_abbreviation'].map(
        lambda x: ABBR_MAPPING.get(x, x))
    
    total_outlook_games += len(outlook_df)
    total_boxscore_games += len(boxscore_df)
    
    # Create matchup keys with mapped abbreviations
    outlook_df['matchup'] = outlook_df['away_abbr_mapped'] + '@' + outlook_df['home_abbr_mapped']
    boxscore_df['matchup'] = boxscore_df['away_team_abbreviation'] + '@' + boxscore_df['home_team_abbreviation']
    
    outlook_matchups = set(outlook_df['matchup'].values)
    boxscore_matchups = set(boxscore_df['matchup'].values)
    
    matched = len(outlook_matchups & boxscore_matchups)
    total_matched += matched
    
    # Track mismatches by date
    if len(outlook_df) != len(boxscore_df):
        date_mismatches.append({
            'date': date,
            'outlook': len(outlook_df),
            'boxscore': len(boxscore_df),
            'diff': len(boxscore_df) - len(outlook_df)
        })
    
    # Check for games in boxscore but not outlook
    boxscore_only = boxscore_matchups - outlook_matchups
    for matchup in boxscore_only:
        game = boxscore_df[boxscore_df['matchup'] == matchup].iloc[0]
        all_boxscore_only.append({
            'date': date,
            'matchup': matchup,
            'game_pk': game['game_pk'],
            'season_type': game['home_season_type']
        })
    
    # Check for games in outlook but not boxscore
    outlook_only = outlook_matchups - boxscore_matchups
    for matchup in outlook_only:
        game = outlook_df[outlook_df['matchup'] == matchup].iloc[0]
        all_outlook_only.append({
            'date': date,
            'matchup': matchup,
            'id': game['id'],
            'season_type': game['season_type']
        })

print(f'{"=" * 80}')
print(f'RESULTS AFTER ABBREVIATION CORRECTION')
print(f'{"=" * 80}')
print(f'Total outlook games:        {total_outlook_games}')
print(f'Total boxscore games:       {total_boxscore_games}')
print(f'Matched games:              {total_matched}')
print(f'Games only in boxscore:     {len(all_boxscore_only)}')
print(f'Games only in outlook:      {len(all_outlook_only)}')
print(f'Dates with count mismatch:  {len(date_mismatches)}')

if date_mismatches:
    print(f'\n{"=" * 80}')
    print(f'DATES WITH GAME COUNT MISMATCHES ({len(date_mismatches)} dates)')
    print(f'{"=" * 80}')
    print(f'\n{"Date":<15} {"Outlook":>8} {"Boxscore":>10} {"Diff":>6}')
    print('-' * 45)
    for dm in date_mismatches[:20]:
        print(f'{dm["date"]:<15} {dm["outlook"]:>8} {dm["boxscore"]:>10} {dm["diff"]:>+6}')
    if len(date_mismatches) > 20:
        print(f'... and {len(date_mismatches) - 20} more dates with mismatches')

if all_boxscore_only:
    print(f'\n{"=" * 80}')
    print(f'GAMES IN BOXSCORE BUT NOT IN OUTLOOK ({len(all_boxscore_only)} games)')
    print(f'{"=" * 80}')
    from collections import Counter
    matchup_counts = Counter(g['matchup'] for g in all_boxscore_only)
    print(f'\nTop 10 matchups:')
    for matchup, count in matchup_counts.most_common(10):
        print(f'  {matchup:<12} {count:>3} games')

if all_outlook_only:
    print(f'\n{"=" * 80}')
    print(f'GAMES IN OUTLOOK BUT NOT IN BOXSCORE ({len(all_outlook_only)} games)')
    print(f'{"=" * 80}')
    from collections import Counter
    matchup_counts = Counter(g['matchup'] for g in all_outlook_only)
    print(f'\nTop 10 matchups:')
    for matchup, count in matchup_counts.most_common(10):
        print(f'  {matchup:<12} {count:>3} games')

# Final verdict
print(f'\n{"=" * 80}')
if len(all_boxscore_only) == 0 and len(all_outlook_only) == 0:
    print('✅ PERFECT MATCH!')
    print('All games align between outlook and boxscores after abbreviation correction')
else:
    print('⚠️  REMAINING MISMATCHES')
    print(f'There are {len(all_boxscore_only)} games in boxscores not found in outlook')
    print(f'There are {len(all_outlook_only)} games in outlook not found in boxscores')
    print(f'Net difference: {abs(len(all_boxscore_only) - len(all_outlook_only))} games')
print(f'{"=" * 80}')
