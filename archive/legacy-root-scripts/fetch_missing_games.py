"""
Fetch the 314 missing games and add them to balldontlie CSVs.
"""

import pandas as pd
import glob
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import time

load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
HEADERS = {"Authorization": API_KEY}

print('=' * 80)
print('FETCHING MISSING GAMES')
print('=' * 80)

# Load MLB official schedule
mlb_df = pd.read_csv('mlb_official_2025_schedule.csv')
mlb_completed = mlb_df[mlb_df['status'].isin(['Final', 'Completed Early'])].copy()

print(f'\nMLB Official: {len(mlb_completed)} games')

# Load corrected balldontlie data
bdl_files = sorted(glob.glob('data/bdl_data/game_outlook/*.csv'))
bdl_df = pd.concat([pd.read_csv(f) for f in bdl_files], ignore_index=True)

print(f'Current balldontlie: {len(bdl_df)} games')
print(f'Missing: {len(mlb_completed) - len(bdl_df)} games')

# Create team name mappings
mlb_to_abbr = {
    'New York Yankees': 'NYY', 'Boston Red Sox': 'BOS', 'Tampa Bay Rays': 'TB',
    'Toronto Blue Jays': 'TOR', 'Baltimore Orioles': 'BAL', 'Cleveland Guardians': 'CLE',
    'Chicago White Sox': 'CHW', 'Detroit Tigers': 'DET', 'Kansas City Royals': 'KC',
    'Minnesota Twins': 'MIN', 'Houston Astros': 'HOU', 'Los Angeles Angels': 'LAA',
    'Seattle Mariners': 'SEA', 'Texas Rangers': 'TEX', 'Athletics': 'OAK',
    'Atlanta Braves': 'ATL', 'Miami Marlins': 'MIA', 'New York Mets': 'NYM',
    'Philadelphia Phillies': 'PHI', 'Washington Nationals': 'WSH', 'Chicago Cubs': 'CHC',
    'Cincinnati Reds': 'CIN', 'Milwaukee Brewers': 'MIL', 'Pittsburgh Pirates': 'PIT',
    'St. Louis Cardinals': 'STL', 'Arizona Diamondbacks': 'ARI', 'Colorado Rockies': 'COL',
    'Los Angeles Dodgers': 'LAD', 'San Diego Padres': 'SD', 'San Francisco Giants': 'SF'
}

# Add abbreviations to MLB data
mlb_completed['away_abbr'] = mlb_completed['away_team_name'].map(mlb_to_abbr)
mlb_completed['home_abbr'] = mlb_completed['home_team_name'].map(mlb_to_abbr)

# Create matchup keys
mlb_completed['matchup_key'] = (
    mlb_completed['date'] + '|' + 
    mlb_completed['away_abbr'] + '|' + 
    mlb_completed['home_abbr']
)

bdl_df['date_only'] = bdl_df['date'].str[:10]
bdl_df['matchup_key'] = (
    bdl_df['date_only'] + '|' + 
    bdl_df['away_team_abbreviation'] + '|' + 
    bdl_df['home_team_abbreviation']
)

# Find missing games
mlb_keys = set(mlb_completed['matchup_key'])
bdl_keys = set(bdl_df['matchup_key'])
missing_keys = mlb_keys - bdl_keys

print(f'\nMissing matchups: {len(missing_keys)}')

# Get full missing game data from MLB
missing_games = mlb_completed[mlb_completed['matchup_key'].isin(missing_keys)].copy()

print(f'\nAttempting to fetch missing games from balldontlie API...')

# Try to fetch each missing game from balldontlie
found_count = 0
not_found_count = 0
missing_from_bdl_api = []

# Group by date to minimize API calls
for date in sorted(missing_games['date'].unique())[:10]:  # Test with first 10 dates
    date_missing = missing_games[missing_games['date'] == date]
    print(f'\n{date}: {len(date_missing)} missing games')
    
    # Fetch all games for this date from balldontlie
    try:
        response = requests.get(
            'https://api.balldontlie.io/mlb/v1/games',
            headers=HEADERS,
            params={'dates[]': date, 'per_page': 100},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bdl_games = data.get('data', [])
            
            # Check each missing game
            for _, missing_game in date_missing.iterrows():
                away_abbr = missing_game['away_abbr']
                home_abbr = missing_game['home_abbr']
                
                # Look for this game in balldontlie response
                found = False
                for bdl_game in bdl_games:
                    bdl_away = bdl_game.get('away_team', {}).get('abbreviation')
                    bdl_home = bdl_game.get('home_team', {}).get('abbreviation')
                    bdl_status = bdl_game.get('status')
                    
                    if bdl_away == away_abbr and bdl_home == home_abbr and bdl_status == 'STATUS_FINAL':
                        print(f'  ✓ Found: {away_abbr} @ {home_abbr}')
                        found_count += 1
                        found = True
                        break
                
                if not found:
                    print(f'  ✗ Not in API: {away_abbr} @ {home_abbr}')
                    not_found_count += 1
                    missing_from_bdl_api.append(missing_game)
        
        time.sleep(0.5)
        
    except Exception as e:
        print(f'  Error fetching date {date}: {e}')

print(f'\n' + '=' * 80)
print(f'SUMMARY OF FIRST 10 DATES:')
print(f'  Found in balldontlie API: {found_count}')
print(f'  Not in balldontlie API: {not_found_count}')
print('=' * 80)

# Strategy: Since many games are missing from balldontlie API, we'll use MLB official data
print('\n\nSTRATEGY: Using MLB Official Schedule data for missing games')
print('=' * 80)

# Create a mapping of balldontlie team IDs (we'll need to infer or use placeholders)
# For now, let's create entries with the data we have from MLB

print('\nWould you like to:')
print('  A) Fill missing games with MLB official data (team names, scores, dates)')
print('  B) Only add games that exist in balldontlie API')
print('  C) Cancel and keep current corrected dataset')
print('\nRecommendation: Option A to get complete 2,434 game dataset')
