"""
Investigate UTC timestamps of games that ended up on wrong dates.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Team abbreviation mapping
ABBR_MAPPING = {
    'ARI': 'AZ',
    'CHW': 'CWS',
    'MIA': 'FLA',
}

print('=' * 80)
print('UTC TIMESTAMP INVESTIGATION')
print('=' * 80)

# List of misplaced games (from previous analysis)
# Format: (boxscore_date, matchup, expected_date_from_outlook)
misplaced_games = [
    ('2009-04-06', 'KC@CWS', '2009-04-07'),
    ('2009-04-06', 'TB@BOS', '2009-04-07'),
    ('2009-04-09', 'OAK@LAA', '2009-04-08'),
    ('2009-04-10', 'PIT@CIN', '2009-04-11'),
    ('2009-04-15', 'PHI@WSH', '2009-04-16'),
    ('2009-04-19', 'STL@CHC', '2009-04-18'),
    ('2009-04-20', 'SD@PHI', '2009-04-19'),
    ('2009-04-20', 'OAK@NYY', '2009-04-21'),
]

outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')

print(f'\nAnalyzing {len(misplaced_games)} sample misplaced games:\n')
print(f'{"Boxscore Date":<15} {"Matchup":<12} {"Outlook Date":<15} {"UTC Timestamp":<22} {"Hour":>5} {"Expected"}')
print('-' * 100)

for boxscore_date, matchup, outlook_date in misplaced_games:
    # Find the game in outlook
    outlook_file = outlook_dir / f'game_outlook_{outlook_date}.csv'
    if outlook_file.exists():
        df = pd.read_csv(outlook_file)
        
        # Apply abbreviation mapping
        df['home_abbr_mapped'] = df['home_team_abbreviation'].map(
            lambda x: ABBR_MAPPING.get(x, x))
        df['away_abbr_mapped'] = df['away_team_abbreviation'].map(
            lambda x: ABBR_MAPPING.get(x, x))
        df['matchup'] = df['away_abbr_mapped'] + '@' + df['home_abbr_mapped']
        
        game = df[df['matchup'] == matchup]
        if not game.empty:
            game = game.iloc[0]
            utc_time = game['date']
            dt = datetime.fromisoformat(utc_time.replace('Z', '+00:00'))
            hour_utc = dt.hour
            
            # Calculate what our heuristic would do
            expected_local = outlook_date if hour_utc < 15 else boxscore_date
            issue = '✓' if expected_local == boxscore_date else '✗ OFF BY 1'
            
            print(f'{boxscore_date:<15} {matchup:<12} {outlook_date:<15} {utc_time:<22} {hour_utc:>5} {issue}')

# Now check a few games that were correctly placed
print(f'\n{"=" * 100}')
print(f'CORRECTLY PLACED GAMES (for comparison)')
print(f'{"=" * 100}\n')

# Load a date with multiple games to see correct ones
correct_date = '2009-04-07'
outlook_file = outlook_dir / f'game_outlook_{correct_date}.csv'
df = pd.read_csv(outlook_file)

print(f'Sample games correctly on {correct_date}:\n')
print(f'{"Matchup":<12} {"UTC Timestamp":<22} {"Hour":>5} {"From Date":>12}')
print('-' * 60)

for idx, row in df.head(5).iterrows():
    away = ABBR_MAPPING.get(row['away_team_abbreviation'], row['away_team_abbreviation'])
    home = ABBR_MAPPING.get(row['home_team_abbreviation'], row['home_team_abbreviation'])
    matchup = f"{away}@{home}"
    utc_time = row['date']
    dt = datetime.fromisoformat(utc_time.replace('Z', '+00:00'))
    hour_utc = dt.hour
    
    # What date does UTC say?
    utc_date = dt.date().isoformat()
    
    print(f'{matchup:<12} {utc_time:<22} {hour_utc:>5} {utc_date:>12}')

print(f'\n{"=" * 100}')
print('ANALYSIS')
print(f'{"=" * 100}')
print(f'''
The misplaced games show a clear pattern:
- Games with hour >= 15 UTC should stay on the UTC date
- Games with hour < 15 UTC should move back 1 day

But some games are being placed on the wrong side of the 15:00 UTC boundary.

The issue is that our heuristic (hour < 15) works well for most games, but:
1. Late night games (after midnight local) appear as early UTC next day
2. Different timezones (ET, CT, MT, PT) have different UTC offsets
3. Some games might have been suspended/resumed

For these 36 games, the balldontlie API has them recorded on dates that don't
match the MLB boxscore dates, likely due to:
- Game start time vs game end time (suspended games)
- Timezone conversion differences
- API data quality issues
''')
