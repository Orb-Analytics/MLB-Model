"""
Comprehensive analysis of all 2009 game outlook vs boxscore mismatches.
Identifies team abbreviation differences and missing games.
"""

import pandas as pd
import glob
from pathlib import Path
from collections import defaultdict

print('=' * 80)
print('COMPREHENSIVE 2009 GAME OUTLOOK VS BOXSCORE ANALYSIS')
print('=' * 80)

# Load all game outlook files
outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
outlook_files = sorted(outlook_dir.glob('game_outlook_*.csv'))

# Load all boxscore files
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')
boxscore_files = sorted(boxscore_dir.glob('boxscores_*.csv'))

# Track abbreviation mappings
abbr_mismatches = defaultdict(set)  # outlook_abbr -> set of boxscore_abbr
team_name_map = {}  # track full names for verification

# Track games only in boxscore or outlook
all_boxscore_only = []
all_outlook_only = []

total_matched = 0
total_outlook_games = 0
total_boxscore_games = 0

print(f'\nProcessing {len(outlook_files)} dates...')

for outlook_file in outlook_files:
    date = outlook_file.stem.split('_')[-1]
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not boxscore_file.exists():
        continue
    
    outlook_df = pd.read_csv(outlook_file)
    boxscore_df = pd.read_csv(boxscore_file)
    
    total_outlook_games += len(outlook_df)
    total_boxscore_games += len(boxscore_df)
    
    # Create matchup keys
    outlook_df['matchup'] = outlook_df['away_team_abbreviation'] + '@' + outlook_df['home_team_abbreviation']
    boxscore_df['matchup'] = boxscore_df['away_team_abbreviation'] + '@' + boxscore_df['home_team_abbreviation']
    
    outlook_matchups = set(outlook_df['matchup'].values)
    boxscore_matchups = set(boxscore_df['matchup'].values)
    
    matched = outlook_matchups & boxscore_matchups
    total_matched += len(matched)
    
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
            'season_type': game['season_type'],
            'utc_time': game['date']
        })
        
        # Try to find similar matchup with different abbreviations
        away, home = matchup.split('@')
        for box_matchup in boxscore_only:
            box_away, box_home = box_matchup.split('@')
            # Check if one team matches and the other might be an abbreviation mismatch
            if (away == box_away and home != box_home) or (away != box_away and home == box_home):
                # Potential abbreviation mismatch
                if away != box_away:
                    abbr_mismatches[away].add(box_away)
                    box_game = boxscore_df[boxscore_df['matchup'] == box_matchup].iloc[0]
                    team_name_map[away] = game['away_team_display_name']
                    team_name_map[box_away] = box_game['away_team_display_name']
                if home != box_home:
                    abbr_mismatches[home].add(box_home)
                    box_game = boxscore_df[boxscore_df['matchup'] == box_matchup].iloc[0]
                    team_name_map[home] = game['home_team_display_name']
                    team_name_map[box_home] = box_game['home_team_display_name']

print(f'\n{"=" * 80}')
print(f'SUMMARY')
print(f'{"=" * 80}')
print(f'Total outlook games:  {total_outlook_games}')
print(f'Total boxscore games: {total_boxscore_games}')
print(f'Matched games:        {total_matched}')
print(f'Games only in boxscore: {len(all_boxscore_only)}')
print(f'Games only in outlook:  {len(all_outlook_only)}')

if abbr_mismatches:
    print(f'\n{"=" * 80}')
    print(f'TEAM ABBREVIATION MISMATCHES')
    print(f'{"=" * 80}')
    for outlook_abbr, boxscore_abbrs in sorted(abbr_mismatches.items()):
        outlook_name = team_name_map.get(outlook_abbr, '?')
        print(f'\n{outlook_name}:')
        print(f'  Outlook uses:  {outlook_abbr}')
        for box_abbr in sorted(boxscore_abbrs):
            box_name = team_name_map.get(box_abbr, '?')
            print(f'  Boxscore uses: {box_abbr} ({box_name})')

if all_boxscore_only:
    print(f'\n{"=" * 80}')
    print(f'GAMES IN BOXSCORE BUT NOT IN OUTLOOK ({len(all_boxscore_only)} total)')
    print(f'{"=" * 80}')
    # Group by matchup to see frequency
    matchup_counts = defaultdict(int)
    for game in all_boxscore_only:
        matchup_counts[game['matchup']] += 1
    
    print('\nTop 10 missing matchups:')
    for matchup, count in sorted(matchup_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f'  {matchup}: {count} games')
    
    print(f'\nFirst 10 missing games:')
    for game in all_boxscore_only[:10]:
        print(f'  {game["date"]}: {game["matchup"]} (game_pk: {game["game_pk"]})')

if all_outlook_only:
    print(f'\n{"=" * 80}')
    print(f'GAMES IN OUTLOOK BUT NOT IN BOXSCORE ({len(all_outlook_only)} total)')
    print(f'{"=" * 80}')
    # Group by matchup
    matchup_counts = defaultdict(int)
    for game in all_outlook_only:
        matchup_counts[game['matchup']] += 1
    
    print('\nTop 10 missing matchups:')
    for matchup, count in sorted(matchup_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f'  {matchup}: {count} games')
    
    print(f'\nFirst 10 missing games:')
    for game in all_outlook_only[:10]:
        print(f'  {game["date"]}: {game["matchup"]} (ID: {game["id"]}, UTC: {game["utc_time"]})')
