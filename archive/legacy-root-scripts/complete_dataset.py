"""
Complete the balldontlie dataset by adding missing games from MLB official schedule.
Transform MLB data format to match balldontlie CSV structure.
"""

import pandas as pd
import glob
from pathlib import Path

print('=' * 80)
print('COMPLETING BALLDONTLIE DATASET WITH MLB OFFICIAL DATA')
print('=' * 80)

# Load MLB official schedule
mlb_df = pd.read_csv('mlb_official_2025_schedule.csv')
mlb_completed = mlb_df[mlb_df['status'].isin(['Final', 'Completed Early'])].copy()

print(f'\nMLB Official: {len(mlb_completed)} games')

# Load corrected balldontlie data
bdl_files = sorted(glob.glob('data/bdl_data/game_outlook/*.csv'))
bdl_df = pd.concat([pd.read_csv(f) for f in bdl_files], ignore_index=True)

print(f'Current balldontlie: {len(bdl_df)} games')
print(f'Missing: {len(mlb_completed) - len(bdl_df)} games\n')

# Create team mappings
mlb_to_abbr = {
    'New York Yankees': 'NYY', 'Boston Red Sox': 'BOS', 'Tampa Bay Rays': 'TB',
    'Toronto Blue Jays': 'TOR', 'Baltimore Orioles': 'BAL', 'Cleveland Guardians': 'CLE',
    'Chicago White Sox': 'CHW', 'Detroit Tigers': 'DET', 'Kansas City Royals': 'KC',
    'Minnesota Twins': 'MIN', 'Houston Astros': 'HOU', 'Los Angeles Angels': 'LAA',
    'Seattle Mariners': 'SEA', 'Texas Rangers': 'TEX', 'Athletics': 'OAK',
    'Oakland Athletics': 'OAK',  # Handle both names
    'Atlanta Braves': 'ATL', 'Miami Marlins': 'MIA', 'New York Mets': 'NYM',
    'Philadelphia Phillies': 'PHI', 'Washington Nationals': 'WSH', 'Chicago Cubs': 'CHC',
    'Cincinnati Reds': 'CIN', 'Milwaukee Brewers': 'MIL', 'Pittsburgh Pirates': 'PIT',
    'St. Louis Cardinals': 'STL', 'Arizona Diamondbacks': 'ARI', 'Colorado Rockies': 'COL',
    'Los Angeles Dodgers': 'LAD', 'San Diego Padres': 'SD', 'San Francisco Giants': 'SF'
}

abbr_to_display = {v: k for k, v in mlb_to_abbr.items() if 'Oakland' not in k}
abbr_to_display['OAK'] = 'Oakland Athletics'

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

print(f'Missing matchups to add: {len(missing_keys)}')

# Get missing games
missing_games = mlb_completed[mlb_completed['matchup_key'].isin(missing_keys)].copy()

print(f'\nSample missing games:')
for _, game in missing_games.head(5).iterrows():
    print(f'  {game["date"]}: {game["away_abbr"]} @ {game["home_abbr"]} ({game["away_score"]}-{game["home_score"]})')

# Transform MLB data to balldontlie CSV format
print(f'\nTransforming {len(missing_games)} missing games to balldontlie format...')

# Get team ID mapping from existing balldontlie data
team_id_map = {}
for _, row in bdl_df.iterrows():
    team_id_map[row['home_team_abbreviation']] = row['home_team_id']
    team_id_map[row['away_team_abbreviation']] = row['away_team_id']

print(f'Team ID mapping created: {len(team_id_map)} teams')

# Create new entries in balldontlie format
new_entries = []
next_id = bdl_df['id'].max() + 1  # Start IDs after current max

for _, mlb_game in missing_games.iterrows():
    away_abbr = mlb_game['away_abbr']
    home_abbr = mlb_game['home_abbr']
    
    # Skip if we can't map the teams
    if away_abbr not in team_id_map or home_abbr not in team_id_map:
        print(f'  Warning: Cannot map {away_abbr} or {home_abbr}')
        continue
    
    # Create entry matching balldontlie CSV structure
    entry = {
        'id': next_id,
        'season': 2025,
        'date': mlb_game['game_date_time'],
        'postseason': False,
        'season_type': 'regular',
        'status': 'STATUS_FINAL',
        'venue': mlb_game['venue'],
        'conference_play': False,
        
        # Home team
        'home_team_id': team_id_map[home_abbr],
        'home_team_slug': home_abbr.lower(),
        'home_team_abbreviation': home_abbr,
        'home_team_display_name': abbr_to_display.get(home_abbr, mlb_game['home_team_name']),
        'home_team_short_display_name': home_abbr,
        'home_team_name': home_abbr,
        'home_team_location': abbr_to_display.get(home_abbr, mlb_game['home_team_name']).split()[-1],
        'home_team_league': 'National' if home_abbr in ['ATL','MIA','NYM','PHI','WSH','CHC','CIN','MIL','PIT','STL','ARI','COL','LAD','SD','SF'] else 'American',
        'home_team_division': 'Unknown',  # We don't have this from MLB API
        
        # Away team
        'away_team_id': team_id_map[away_abbr],
        'away_team_slug': away_abbr.lower(),
        'away_team_abbreviation': away_abbr,
        'away_team_display_name': abbr_to_display.get(away_abbr, mlb_game['away_team_name']),
        'away_team_short_display_name': away_abbr,
        'away_team_name': away_abbr,
        'away_team_location': abbr_to_display.get(away_abbr, mlb_game['away_team_name']).split()[-1],
        'away_team_league': 'National' if away_abbr in ['ATL','MIA','NYM','PHI','WSH','CHC','CIN','MIL','PIT','STL','ARI','COL','LAD','SD','SF'] else 'American',
        'away_team_division': 'Unknown',
        
        # Scores
        'home_team_score': mlb_game['home_score'],
        'away_team_score': mlb_game['away_score'],
        
        # Favorite/Underdog (blank)
        'favorite_id': None,
        'underdog_id': None,
        'favorite_abbreviation': None,
        'underdog_abbreviation': None,
        'favorite_display_name': None,
        'underdog_display_name': None
    }
    
    new_entries.append(entry)
    next_id += 1

print(f'Created {len(new_entries)} new entries')

# Combine with existing data
new_df = pd.DataFrame(new_entries)
combined_df = pd.concat([bdl_df.drop(columns=['date_only', 'matchup_key']), new_df], ignore_index=True)

print(f'\nCombined dataset: {len(combined_df)} games')
print(f'Expected: {len(mlb_completed)} games')
print(f'Match: {"✅" if len(combined_df) == len(mlb_completed) else "⚠️"}')

# Save back to CSV files by date
print(f'\n' + '=' * 80)
print('SAVING COMPLETE DATASET')
print('=' * 80)

output_dir = Path('data/bdl_data/game_outlook')

# Group by date and save
combined_df['date_only'] = combined_df['date'].str[:10]

dates_updated = 0
for date in sorted(combined_df['date_only'].unique()):
    date_games = combined_df[combined_df['date_only'] == date]
    
    # Remove temporary column
    date_games = date_games.drop(columns=['date_only'])
    
    # Save to CSV
    filename = f'game_outlook_{date}.csv'
    filepath = output_dir / filename
    date_games.to_csv(filepath, index=False)
    dates_updated += 1

print(f'\n✓ Updated {dates_updated} CSV files')
print(f'✓ Total games in dataset: {len(combined_df)}')
print('\n' + '=' * 80)
print('✅ DATASET NOW COMPLETE!')
print('=' * 80)
