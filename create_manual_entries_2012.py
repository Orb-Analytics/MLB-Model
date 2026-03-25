import pandas as pd
import glob

# Missing game_pks
missing_games = [
    (320154, 'CIN', 'STL', 0, 1, '2012-10-03'),
    (320156, 'DET', 'KC', 1, 0, '2012-10-03'),
    (320161, 'SD', 'MIL', 7, 6, '2012-10-03'),
]

# Read all MLB boxscores to find these games
all_boxscores = []
for file in sorted(glob.glob('data/2012_data/mlb_data/raw/boxscores/*.csv')):
    df = pd.read_csv(file)
    all_boxscores.append(df)

boxscores_df = pd.concat(all_boxscores, ignore_index=True)
print(f"Total MLB boxscores: {len(boxscores_df)}")

# Read a sample BDL file to understand the structure
sample_bdl = pd.read_csv('data/2012_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_2012-04-05.csv')
print(f"\nBDL columns: {list(sample_bdl.columns)[:10]}...")

# Team metadata mapping (from existing BDL data or defined)
team_info = {
    'CIN': {'id': 6, 'slug': 'cincinnati-reds', 'display_name': 'Cincinnati Reds', 'short_name': 'Reds', 'name': 'Reds', 'location': 'Cincinnati', 'league': 'National', 'division': 'Central'},
    'STL': {'id': 26, 'slug': 'st-louis-cardinals', 'display_name': 'St. Louis Cardinals', 'short_name': 'Cardinals', 'name': 'Cardinals', 'location': 'St. Louis', 'league': 'National', 'division': 'Central'},
    'DET': {'id': 9, 'slug': 'detroit-tigers', 'display_name': 'Detroit Tigers', 'short_name': 'Tigers', 'name': 'Tigers', 'location': 'Detroit', 'league': 'American', 'division': 'Central'},
    'KC': {'id': 12, 'slug': 'kansas-city-royals', 'display_name': 'Kansas City Royals', 'short_name': 'Royals', 'name': 'Royals', 'location': 'Kansas City', 'league': 'American', 'division': 'Central'},
    'SD': {'id': 23, 'slug': 'san-diego-padres', 'display_name': 'San Diego Padres', 'short_name': 'Padres', 'name': 'Padres', 'location': 'San Diego', 'league': 'National', 'division': 'West'},
    'MIL': {'id': 15, 'slug': 'milwaukee-brewers', 'display_name': 'Milwaukee Brewers', 'short_name': 'Brewers', 'name': 'Brewers', 'location': 'Milwaukee', 'league': 'National', 'division': 'Central'},
}

# Venue mapping
venue_map = {
    'STL': 'Busch Stadium',
    'KC': 'Kauffman Stadium',
    'MIL': 'Miller Park',
}

# Find highest existing ID in BDL data
max_id = 0
for file in glob.glob('data/2012_data/mlb_data/raw/bdl_data/game_outlook/*.csv'):
    df = pd.read_csv(file)
    if len(df) > 0 and 'id' in df.columns:
        file_max = df['id'].max()
        if file_max > max_id:
            max_id = file_max

print(f"\nHighest existing BDL ID: {max_id}")

# Create manual entries
manual_entries = []
start_id = max_id + 1

for idx, (game_pk, away_abbr, home_abbr, away_score, home_score, game_date) in enumerate(missing_games):
    # Find the game in MLB boxscores
    game_row = boxscores_df[boxscores_df['game_pk'] == game_pk]
    
    if len(game_row) == 0:
        print(f"WARNING: Game {game_pk} not found in MLB boxscores!")
        continue
    
    game_row = game_row.iloc[0]
    
    # Extract venue from MLB data if available
    venue = venue_map.get(home_abbr, '')
    
    # Get team info
    away_info = team_info[away_abbr]
    home_info = team_info[home_abbr]
    
    # Create entry in BDL format
    entry = {
        'id': start_id + idx,
        'game_pk': game_pk,
        'season': 2012,
        'date': f"{game_date}T00:00:00.000Z",
        'postseason': False,
        'season_type': 'regular',
        'status': 'STATUS_FINAL',
        'venue': venue,
        'conference_play': False,
        'home_team_id': home_info['id'],
        'away_team_id': away_info['id'],
        'home_team_slug': home_info['slug'],
        'away_team_slug': away_info['slug'],
        'home_team_abbreviation': home_abbr,
        'away_team_abbreviation': away_abbr,
        'home_team_display_name': home_info['display_name'],
        'away_team_display_name': away_info['display_name'],
        'home_team_short_display_name': home_info['short_name'],
        'away_team_short_display_name': away_info['short_name'],
        'home_team_name': home_info['name'],
        'away_team_name': away_info['name'],
        'home_team_location': home_info['location'],
        'away_team_location': away_info['location'],
        'home_team_league': home_info['league'],
        'away_team_league': away_info['league'],
        'home_team_division': home_info['division'],
        'away_team_division': away_info['division'],
        'home_team_score': home_score,
        'away_team_score': away_score,
        'favorite_id': '',
        'underdog_id': '',
        'favorite_abbreviation': '',
        'underdog_abbreviation': '',
        'favorite_display_name': '',
        'underdog_display_name': '',
    }
    
    manual_entries.append(entry)
    print(f"Created entry {start_id + idx} for game {game_pk}: {away_abbr} @ {home_abbr} = {away_score}-{home_score} on {game_date}")

# Save the manual entries to a CSV
manual_df = pd.DataFrame(manual_entries)
manual_df.to_csv('manual_entries_2012.csv', index=False)
print(f"\nCreated {len(manual_entries)} manual entries")
print(f"Saved to manual_entries_2012.csv")
