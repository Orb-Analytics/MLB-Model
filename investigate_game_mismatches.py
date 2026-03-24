"""
Investigate which specific games are in boxscores but not in game outlook for 2009.
"""

import pandas as pd
from pathlib import Path

print('=' * 80)
print('INVESTIGATING GAME MISMATCHES - APRIL 6, 2009')
print('=' * 80)

# Load April 6 data from both sources
date = '2009-04-06'
outlook_file = Path(f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv')
boxscore_file = Path(f'data/2009_data/mlb_data/raw/boxscores/boxscores_{date}.csv')

print(f'\nLoading {date} data...')
outlook_df = pd.read_csv(outlook_file)
boxscore_df = pd.read_csv(boxscore_file)

print(f'Game outlook games: {len(outlook_df)}')
print(f'Boxscore games:     {len(boxscore_df)}')
print(f'Difference:         {len(boxscore_df) - len(outlook_df)}')

# Create matchup keys (away_team @ home_team)
outlook_df['matchup'] = outlook_df['away_team_abbreviation'] + '@' + outlook_df['home_team_abbreviation']
boxscore_df['matchup'] = boxscore_df['away_team_abbreviation'] + '@' + boxscore_df['home_team_abbreviation']

outlook_matchups = set(outlook_df['matchup'].values)
boxscore_matchups = set(boxscore_df['matchup'].values)

print(f'\nMatchups in both:     {len(outlook_matchups & boxscore_matchups)}')
print(f'Only in outlook:      {len(outlook_matchups - boxscore_matchups)}')
print(f'Only in boxscore:     {len(boxscore_matchups - outlook_matchups)}')

# Show games only in boxscore
boxscore_only = boxscore_matchups - outlook_matchups
if boxscore_only:
    print(f'\n{"=" * 80}')
    print(f'GAMES IN BOXSCORE BUT NOT IN OUTLOOK ({len(boxscore_only)} games):')
    print(f'{"=" * 80}')
    for matchup in sorted(boxscore_only):
        game = boxscore_df[boxscore_df['matchup'] == matchup].iloc[0]
        print(f'\nGame {game["game_pk"]}: {matchup}')
        print(f'  Score: {int(game["away_batting_r"])} - {int(game["home_batting_r"])}')
        print(f'  Season type: {game["home_season_type"]}')
        print(f'  Postseason: {game["home_postseason"]}')

# Show games only in outlook
outlook_only = outlook_matchups - boxscore_matchups
if outlook_only:
    print(f'\n{"=" * 80}')
    print(f'GAMES IN OUTLOOK BUT NOT IN BOXSCORE ({len(outlook_only)} games):')
    print(f'{"=" * 80}')
    for matchup in sorted(outlook_only):
        game = outlook_df[outlook_df['matchup'] == matchup].iloc[0]
        print(f'\nGame {game["id"]}: {matchup}')
        print(f'  Scores: {game["away_team_score"]} - {game["home_team_score"]}')
        print(f'  Status: {game["status"]}')
        print(f'  Season type: {game["season_type"]}')
        print(f'  UTC timestamp: {game["date"]}')

# Compare matched games
matched = outlook_matchups & boxscore_matchups
if matched:
    print(f'\n{"=" * 80}')
    print(f'MATCHED GAMES ({len(matched)} games):')
    print(f'{"=" * 80}')
    for matchup in sorted(list(matched))[:5]:
        outlook_game = outlook_df[outlook_df['matchup'] == matchup].iloc[0]
        boxscore_game = boxscore_df[boxscore_df['matchup'] == matchup].iloc[0]
        print(f'\n{matchup}')
        print(f'  Outlook: {outlook_game["away_team_score"]}-{outlook_game["home_team_score"]} (ID: {outlook_game["id"]})')
        print(f'  Boxscore: {int(boxscore_game["away_batting_r"])}-{int(boxscore_game["home_batting_r"])} (game_pk: {boxscore_game["game_pk"]})')
    if len(matched) > 5:
        print(f'  ... and {len(matched) - 5} more matched games')
