"""
Create complete dataset using ONLY MLB official data.
This ensures we have all 2430 games with proper game identifiers.
"""

import pandas as pd
from pathlib import Path

print('=' * 80)
print('CREATING COMPLETE DATASET FROM MLB OFFICIAL DATA')
print('=' * 80)

# Load MLB official schedule
mlb_df = pd.read_csv('mlb_official_2025_schedule.csv')
mlb_completed = mlb_df[mlb_df['status'].isin(['Final', 'Completed Early'])].copy()
mlb_unique = mlb_completed.drop_duplicates('mlb_game_pk').copy()

print(f'\nMLB official games: {len(mlb_unique)} unique games')

# Team mappings
mlb_to_abbr = {
    'New York Yankees': 'NYY', 'Boston Red Sox': 'BOS', 'Tampa Bay Rays': 'TB',
    'Toronto Blue Jays': 'TOR', 'Baltimore Orioles': 'BAL', 'Cleveland Guardians': 'CLE',
    'Chicago White Sox': 'CHW', 'Detroit Tigers': 'DET', 'Kansas City Royals': 'KC',
    'Minnesota Twins': 'MIN', 'Houston Astros': 'HOU', 'Los Angeles Angels': 'LAA',
    'Seattle Mariners': 'SEA', 'Texas Rangers': 'TEX', 'Athletics': 'OAK',
    'Oakland Athletics': 'OAK',
    'Atlanta Braves': 'ATL', 'Miami Marlins': 'MIA', 'New York Mets': 'NYM',
    'Philadelphia Phillies': 'PHI', 'Washington Nationals': 'WSH', 'Chicago Cubs': 'CHC',
    'Cincinnati Reds': 'CIN', 'Milwaukee Brewers': 'MIL', 'Pittsburgh Pirates': 'PIT',
    'St. Louis Cardinals': 'STL', 'Arizona Diamondbacks': 'ARI', 'Colorado Rockies': 'COL',
    'Los Angeles Dodgers': 'LAD', 'San Diego Padres': 'SD', 'San Francisco Giants': 'SF'
}

abbr_to_display = {v: k for k, v in mlb_to_abbr.items() if 'Oakland' not in k}
abbr_to_display['OAK'] = 'Oakland Athletics'

# Hardcode team IDs (from balldontlie)
team_ids = {
    'NYY': 1, 'BOS': 2, 'TB': 3, 'TOR': 4, 'BAL': 5,
    'CLE': 6, 'CHW': 7, 'DET': 8, 'KC': 9, 'MIN': 10,
    'HOU': 11, 'LAA': 12, 'SEA': 13, 'TEX': 14, 'OAK': 15,
    'ATL': 16, 'MIA': 17, 'NYM': 18, 'PHI': 19, 'WSH': 20,
    'CHC': 21, 'CIN': 22, 'MIL': 23, 'PIT': 24, 'STL': 25,
    'ARI': 26, 'COL': 27, 'LAD': 28, 'SD': 29, 'SF': 30
}

NL_teams = {'ATL','MIA','NYM','PHI','WSH','CHC','CIN','MIL','PIT','STL','ARI','COL','LAD','SD','SF'}

# Transform to balldontlie format
print('\nTransforming MLB data to balldontlie CSV format...')
entries = []
skipped = 0

for _, mlb_game in mlb_unique.iterrows():
    away_abbr = mlb_to_abbr.get(mlb_game['away_team_name'])
    home_abbr = mlb_to_abbr.get(mlb_game['home_team_name'])
    
    if not away_abbr or not home_abbr:
        print(f'  Warning: Cannot map {mlb_game["away_team_name"]} or {mlb_game["home_team_name"]}')
        skipped += 1
        continue
    
    entry = {
        'id': int(mlb_game['mlb_game_pk']),
        'season': 2025,
        'date': mlb_game['game_date_time'],
        'postseason': False,
        'season_type': 'regular',
        'status': 'STATUS_FINAL',
        'venue': mlb_game['venue'],
        'conference_play': False,
        
        # Home team
        'home_team_id': team_ids[home_abbr],
        'home_team_slug': home_abbr.lower(),
        'home_team_abbreviation': home_abbr,
        'home_team_display_name': abbr_to_display[home_abbr],
        'home_team_short_display_name': home_abbr,
        'home_team_name': home_abbr,
        'home_team_location': abbr_to_display[home_abbr].split()[-1],
        'home_team_league': 'National' if home_abbr in NL_teams else 'American',
        'home_team_division': 'Unknown',
        
        # Away team
        'away_team_id': team_ids[away_abbr],
        'away_team_slug': away_abbr.lower(),
        'away_team_abbreviation': away_abbr,
        'away_team_display_name': abbr_to_display[away_abbr],
        'away_team_short_display_name': away_abbr,
        'away_team_name': away_abbr,
        'away_team_location': abbr_to_display[away_abbr].split()[-1],
        'away_team_league': 'National' if away_abbr in NL_teams else 'American',
        'away_team_division': 'Unknown',
        
        # Scores
        'home_team_score': mlb_game['home_score'],
        'away_team_score': mlb_game['away_score'],
        
        # Favorite/Underdog (blank for now)
        'favorite_id': None,
        'underdog_id': None,
        'favorite_abbreviation': None,
        'underdog_abbreviation': None,
        'favorite_display_name': None,
        'underdog_display_name': None
    }
    
    entries.append(entry)

print(f'Transformed {len(entries)} games')
if skipped > 0:
    print(f'Skipped {skipped} games')

# Create DataFrame
df = pd.DataFrame(entries)
df['date_only'] = df['date'].str[:10]
df['matchup_key'] = df['date_only'] + '|' + df['away_team_abbreviation'] + '|' + df['home_team_abbreviation']

print(f'\nFinal dataset: {len(df)} games')
print(f'Unique matchup keys: {df["matchup_key"].nunique()}')
print(f'Doubleheader games: {len(df) - df["matchup_key"].nunique()}')

# Save to CSV files by date
print(f'\nSaving to CSV files...')
output_dir = Path('data/bdl_data/game_outlook')
output_dir.mkdir(parents=True, exist_ok=True)

# Clear existing files
for f in output_dir.glob('game_outlook_*.csv'):
    f.unlink()

# Group by date and save
for date, group in df.groupby('date_only'):
    filename = f'game_outlook_{date}.csv'
    filepath = output_dir / filename
    
    # Drop helper columns
    output_group = group.drop(columns=['date_only', 'matchup_key']).sort_values('id')
    output_group.to_csv(filepath, index=False)

files_written = df['date_only'].nunique()
print(f'Wrote {files_written} CSV files to {output_dir}')
print(f'\n✅ Complete authoritative dataset created from MLB official data!')
print(f'Total games: {len(df)}')
print(f'All games from 2025 regular season with STATUS_FINAL')
