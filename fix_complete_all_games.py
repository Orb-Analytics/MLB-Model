"""
Fix duplicates and properly complete the dataset including doubleheaders.

Step 1: Remove duplicate matchup keys (keep original balldontlie where possible)
Step 2: Match balldontlie games to MLB by game_pk
Step 3: Add ALL missing MLB games (including both games of doubleheaders)
"""

import pandas as pd
import glob
from pathlib import Path

print('=' * 80)
print('FIXING DUPLICATES AND ADDING MISSING GAMES (INCLUDING DOUBLEHEADERS)')
print('=' * 80)

# Load data
mlb_df = pd.read_csv('mlb_official_2025_schedule.csv')
mlb_completed = mlb_df[mlb_df['status'].isin(['Final', 'Completed Early'])].copy()
mlb_unique = mlb_completed.drop_duplicates('mlb_game_pk').copy()

bdl_files = sorted(glob.glob('data/bdl_data/game_outlook/*.csv'))
bdl_df = pd.concat([pd.read_csv(f) for f in bdl_files], ignore_index=True)

print(f'\nStarting balldontlie: {len(bdl_df)} games')
print(f'MLB games to match: {len(mlb_unique)} games')

# Create matchup keys
bdl_df['date_only'] = bdl_df['date'].str[:10]
bdl_df['matchup_key'] = (
    bdl_df['date_only'] + '|' + 
    bdl_df['away_team_abbreviation'] + '|' + 
    bdl_df['home_team_abbreviation']
)

print(f'balldontlie unique matchup keys: {bdl_df["matchup_key"].nunique()}')
print(f'balldontlie duplicates: {len(bdl_df) - bdl_df["matchup_key"].nunique()}')

# Step 1: Remove duplicates, keeping the one with lowest ID (original balldontlie)
print('\nStep 1: Removing duplicates from balldontlie...')
bdl_deduplicated = bdl_df.sort_values('id').drop_duplicates('matchup_key', keep='first').copy()
print(f'After deduplication: {len(bdl_deduplicated)} games')
print(f'Removed: {len(bdl_df) - len(bdl_deduplicated)} duplicate games')

# Step 2: Match by game_pk (balldontlie uses MLB game_pk as ID)
print('\nStep 2: Matching balldontlie games to MLB by game_pk/ID...')
bdl_game_pks = set(bdl_deduplicated['id'].astype(int))
mlb_game_pks = set(mlb_unique['mlb_game_pk'].astype(int))

matched = bdl_game_pks & mlb_game_pks
missing_pks = mlb_game_pks - bdl_game_pks

print(f'Matched by game_pk: {len(matched)} games')
print(f'Missing from balldontlie: {len(missing_pks)} games')

# Step 3: Add ALL missing games
print(f'\nStep 3: Adding {len(missing_pks)} missing games...')

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

# Get team ID mapping from balldontlie
team_id_map = {}
for _, row in bdl_deduplicated.iterrows():
    team_id_map[row['home_team_abbreviation']] = row['home_team_id']
    team_id_map[row['away_team_abbreviation']] = row['away_team_id']

# Add missing games
missing_games = mlb_unique[mlb_unique['mlb_game_pk'].isin(missing_pks)].copy()
new_entries = []
skipped = 0

for _, mlb_game in missing_games.iterrows():
    away_abbr = mlb_to_abbr.get(mlb_game['away_team_name'])
    home_abbr = mlb_to_abbr.get(mlb_game['home_team_name'])
    
    # Skip if we can't map the teams
    if not away_abbr or not home_abbr:
        print(f'  Warning: Cannot map {mlb_game["away_team_name"]} or {mlb_game["home_team_name"]}')
        skipped += 1
        continue
        
    if away_abbr not in team_id_map or home_abbr not in team_id_map:
        print(f'  Warning: No team ID for {away_abbr} or {home_abbr}')
        skipped += 1
        continue
    
    entry = {
        'id': int(mlb_game['mlb_game_pk']),  # Use MLB game_pk as ID
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
        'home_team_division': 'Unknown',
        
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

print(f'Created {len(new_entries)} new entries')
if skipped > 0:
    print(f'Skipped {skipped} games due to team mapping issues')

# Combine datasets
new_df = pd.DataFrame(new_entries)
combined_df = pd.concat([
    bdl_deduplicated.drop(columns=['date_only', 'matchup_key']),
    new_df
], ignore_index=True)

print(f'\nFinal dataset: {len(combined_df)} games')
print(f'MLB target: {len(mlb_unique)} games')
print(f'Match: {"✅" if len(combined_df) == len(mlb_unique) else f"⚠️  Still missing: {len(mlb_unique) - len(combined_df)}"} ')

# Verify matchup keys and doubleheaders
combined_df['date_only'] = combined_df['date'].str[:10]
combined_df['matchup_key'] = (
    combined_df['date_only'] + '|' + 
    combined_df['away_team_abbreviation'] + '|' + 
    combined_df['home_team_abbreviation']
)

unique_matchups = combined_df['matchup_key'].nunique()
total_games = len(combined_df)
doubleheaders = total_games - unique_matchups

print(f'\nUnique matchup keys: {unique_matchups}')
print(f'Doubleheader games: {doubleheaders} (should be 28)')

# Save back to CSV files by date
print(f'\nSaving to CSV files...')
output_dir = Path('data/bdl_data/game_outlook')

# Group by date and save
combined_df['file_date'] = combined_df['date_only']
for date, group in combined_df.groupby('file_date'):
    filename = f'game_outlook_{date}.csv'
    filepath = output_dir / filename
    
    # Sort by game ID and drop helper columns
    output_group = group.drop(columns=['date_only', 'matchup_key', 'file_date']).sort_values('id')
    output_group.to_csv(filepath, index=False)

files_written = len(combined_df['file_date'].unique())
print(f'Wrote {files_written} CSV files to {output_dir}')
print(f'\n✅ Dataset complete!')
print(f'Total games: {len(combined_df)}')
print(f'Unique matchups: {unique_matchups}')
print(f'Doubleheaders: {doubleheaders}')
