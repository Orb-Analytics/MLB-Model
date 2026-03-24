"""
Detailed investigation of the 37 games in boxscores but not in game outlook.
"""

import pandas as pd
import glob
from pathlib import Path
from collections import defaultdict

# Team abbreviation mapping: balldontlie -> MLB historical
ABBR_MAPPING = {
    'ARI': 'AZ',   # Arizona Diamondbacks
    'CHW': 'CWS',  # Chicago White Sox
    'MIA': 'FLA',  # Florida Marlins (2009)
}

print('=' * 80)
print('DETAILED INVESTIGATION OF 37 MISSING GAMES')
print('=' * 80)

# Load all game outlook files
outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
outlook_files = sorted(outlook_dir.glob('game_outlook_*.csv'))

# Load all boxscore files
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')
boxscore_files = sorted(boxscore_dir.glob('boxscores_*.csv'))

missing_games = []

print(f'\nProcessing {len(outlook_files)} dates...\n')

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
    
    # Create matchup keys with mapped abbreviations
    outlook_df['matchup'] = outlook_df['away_abbr_mapped'] + '@' + outlook_df['home_abbr_mapped']
    boxscore_df['matchup'] = boxscore_df['away_team_abbreviation'] + '@' + boxscore_df['home_team_abbreviation']
    
    outlook_matchups = set(outlook_df['matchup'].values)
    boxscore_matchups = set(boxscore_df['matchup'].values)
    
    # Find games in boxscore but not outlook
    boxscore_only = boxscore_matchups - outlook_matchups
    for matchup in boxscore_only:
        game = boxscore_df[boxscore_df['matchup'] == matchup].iloc[0]
        
        # Get detailed game info
        game_info = {
            'date': date,
            'game_pk': game['game_pk'],
            'matchup': matchup,
            'away_team': game['away_team_abbreviation'],
            'home_team': game['home_team_abbreviation'],
            'away_score': int(game['away_batting_r']),
            'home_score': int(game['home_batting_r']),
            'season_type': game['home_season_type'],
            'postseason': game['home_postseason'],
            'away_gp': game['away_gp'],
            'home_gp': game['home_gp'],
        }
        
        # Check if same matchup exists on nearby dates in outlook
        nearby_dates = []
        for date_offset in [-1, 0, 1]:
            from datetime import datetime, timedelta
            check_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=date_offset)).strftime('%Y-%m-%d')
            check_file = outlook_dir / f'game_outlook_{check_date}.csv'
            if check_file.exists():
                check_df = pd.read_csv(check_file)
                check_df['home_abbr_mapped'] = check_df['home_team_abbreviation'].map(
                    lambda x: ABBR_MAPPING.get(x, x))
                check_df['away_abbr_mapped'] = check_df['away_team_abbreviation'].map(
                    lambda x: ABBR_MAPPING.get(x, x))
                check_df['matchup'] = check_df['away_abbr_mapped'] + '@' + check_df['home_abbr_mapped']
                
                if matchup in check_df['matchup'].values:
                    nearby_dates.append(check_date)
        
        game_info['found_on_other_dates'] = nearby_dates
        missing_games.append(game_info)

print(f'{"=" * 80}')
print(f'FOUND {len(missing_games)} GAMES IN BOXSCORE BUT NOT IN OUTLOOK')
print(f'{"=" * 80}')

# Group by date
from collections import Counter
date_counts = Counter(g['date'] for g in missing_games)
print(f'\nGames by date:')
for date, count in sorted(date_counts.items())[:15]:
    print(f'  {date}: {count} game(s)')
if len(date_counts) > 15:
    print(f'  ... and {len(date_counts) - 15} more dates')

# Group by matchup
matchup_counts = Counter(g['matchup'] for g in missing_games)
print(f'\nGames by matchup (top 15):')
for matchup, count in matchup_counts.most_common(15):
    print(f'  {matchup:<15} {count} game(s)')

# Check for patterns
print(f'\n{"=" * 80}')
print(f'PATTERN ANALYSIS')
print(f'{"=" * 80}')

# Check if these are doubleheaders
print(f'\nDoubleheader check:')
doubleheader_dates = {}
for game in missing_games:
    key = (game['date'], game['matchup'])
    if key not in doubleheader_dates:
        doubleheader_dates[key] = []
    doubleheader_dates[key].append(game['game_pk'])

multiple_games = [(k, v) for k, v in doubleheader_dates.items() if len(v) > 1]
if multiple_games:
    print(f'  Found {len(multiple_games)} doubleheaders in missing games:')
    for (date, matchup), game_pks in multiple_games[:5]:
        print(f'    {date}: {matchup} - games {game_pks}')
else:
    print(f'  No doubleheaders detected in missing games')

# Check if found on different dates
found_elsewhere = [g for g in missing_games if g['found_on_other_dates']]
print(f'\nGames found on different dates in outlook: {len(found_elsewhere)}')
if found_elsewhere:
    for game in found_elsewhere[:10]:
        print(f'  {game["matchup"]} on {game["date"]} (boxscore) -> outlook has it on {game["found_on_other_dates"]}')
    if len(found_elsewhere) > 10:
        print(f'  ... and {len(found_elsewhere) - 10} more')

# Show detailed list of all missing games
print(f'\n{"=" * 80}')
print(f'COMPLETE LIST OF 37 MISSING GAMES')
print(f'{"=" * 80}')
print(f'\n{"Date":<12} {"Game PK":<8} {"Matchup":<12} {"Score":<8} {"GP(A/H)":<10} {"Notes"}')
print('-' * 80)

for game in sorted(missing_games, key=lambda x: (x['date'], x['game_pk'])):
    score = f"{game['away_score']}-{game['home_score']}"
    gp = f"{game['away_gp']}/{game['home_gp']}"
    notes = ''
    if game['found_on_other_dates']:
        notes = f"Found on: {', '.join(game['found_on_other_dates'])}"
    
    print(f"{game['date']:<12} {game['game_pk']:<8} {game['matchup']:<12} {score:<8} {gp:<10} {notes}")

# Summary statistics
print(f'\n{"=" * 80}')
print(f'SUMMARY')
print(f'{"=" * 80}')
print(f'Total missing games: {len(missing_games)}')
print(f'Unique dates: {len(date_counts)}')
print(f'Unique matchups: {len(matchup_counts)}')
print(f'Games on wrong date in outlook: {len(found_elsewhere)}')
print(f'Truly missing from outlook: {len(missing_games) - len(found_elsewhere)}')
