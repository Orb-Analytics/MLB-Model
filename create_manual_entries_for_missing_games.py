import pandas as pd
import glob
from datetime import datetime

# Missing game_pks
missing_games = [
    (289037, 'LAD', 'WSH', 0, 0, '2011-09-08'),
    (289311, 'CHC', 'SD', 2, 9, '2011-09-28'),
    (289315, 'KC', 'MIN', 0, 1, '2011-09-28'),
    (289316, 'LAD', 'ARI', 7, 5, '2011-09-28'),
    (289318, 'OAK', 'SEA', 2, 0, '2011-09-28'),
    (289320, 'PIT', 'MIL', 3, 7, '2011-09-28'),
    (289321, 'STL', 'HOU', 8, 0, '2011-09-28'),
    (289322, 'TEX', 'LAA', 3, 1, '2011-09-28'),
]

# Read all MLB boxscores to find these games
all_boxscores = []
for file in sorted(glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv')):
    df = pd.read_csv(file)
    all_boxscores.append(df)

boxscores_df = pd.concat(all_boxscores, ignore_index=True)
print(f"Total MLB boxscores: {len(boxscores_df)}")

# Read an existing BDL file to understand the structure
sample_bdl = pd.read_csv('data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_2011-04-02.csv')
print(f"\nBDL columns: {list(sample_bdl.columns)}")

# Team metadata mapping (from existing BDL data)
team_info = {
    'ARI': {'id': 1, 'slug': 'arizona-diamondbacks', 'display_name': 'Arizona Diamondbacks', 'short_name': 'Diamondbacks', 'name': 'Diamondbacks', 'location': 'Arizona', 'league': 'National', 'division': 'West'},
    'LAD': {'id': 14, 'slug': 'los-angeles-dodgers', 'display_name': 'Los Angeles Dodgers', 'short_name': 'Dodgers', 'name': 'Dodgers', 'location': 'Los Angeles', 'league': 'National', 'division': 'West'},
    'WSH': {'id': 29, 'slug': 'washington-nationals', 'display_name': 'Washington Nationals', 'short_name': 'Nationals', 'name': 'Nationals', 'location': 'Washington', 'league': 'National', 'division': 'East'},
    'CHC': {'id': 7, 'slug': 'chicago-cubs', 'display_name': 'Chicago Cubs', 'short_name': 'Cubs', 'name': 'Cubs', 'location': 'Chicago', 'league': 'National', 'division': 'Central'},
    'SD': {'id': 23, 'slug': 'san-diego-padres', 'display_name': 'San Diego Padres', 'short_name': 'Padres', 'name': 'Padres', 'location': 'San Diego', 'league': 'National', 'division': 'West'},
    'KC': {'id': 12, 'slug': 'kansas-city-royals', 'display_name': 'Kansas City Royals', 'short_name': 'Royals', 'name': 'Royals', 'location': 'Kansas City', 'league': 'American', 'division': 'Central'},
    'MIN': {'id': 16, 'slug': 'minnesota-twins', 'display_name': 'Minnesota Twins', 'short_name': 'Twins', 'name': 'Twins', 'location': 'Minnesota', 'league': 'American', 'division': 'Central'},
    'OAK': {'id': 20, 'slug': 'oakland-athletics', 'display_name': 'Oakland Athletics', 'short_name': 'Athletics', 'name': 'Athletics', 'location': 'Oakland', 'league': 'American', 'division': 'West'},
    'SEA': {'id': 25, 'slug': 'seattle-mariners', 'display_name': 'Seattle Mariners', 'short_name': 'Mariners', 'name': 'Mariners', 'location': 'Seattle', 'league': 'American', 'division': 'West'},
    'PIT': {'id': 21, 'slug': 'pittsburgh-pirates', 'display_name': 'Pittsburgh Pirates', 'short_name': 'Pirates', 'name': 'Pirates', 'location': 'Pittsburgh', 'league': 'National', 'division': 'Central'},
    'MIL': {'id': 15, 'slug': 'milwaukee-brewers', 'display_name': 'Milwaukee Brewers', 'short_name': 'Brewers', 'name': 'Brewers', 'location': 'Milwaukee', 'league': 'National', 'division': 'Central'},
    'STL': {'id': 26, 'slug': 'st-louis-cardinals', 'display_name': 'St. Louis Cardinals', 'short_name': 'Cardinals', 'name': 'Cardinals', 'location': 'St. Louis', 'league': 'National', 'division': 'Central'},
    'HOU': {'id': 10, 'slug': 'houston-astros', 'display_name': 'Houston Astros', 'short_name': 'Astros', 'name': 'Astros', 'location': 'Houston', 'league': 'National', 'division': 'Central'},
    'TEX': {'id': 27, 'slug': 'texas-rangers', 'display_name': 'Texas Rangers', 'short_name': 'Rangers', 'name': 'Rangers', 'location': 'Texas', 'league': 'American', 'division': 'West'},
    'LAA': {'id': 13, 'slug': 'los-angeles-angels', 'display_name': 'Los Angeles Angels', 'short_name': 'Angels', 'name': 'Angels', 'location': 'Los Angeles', 'league': 'American', 'division': 'West'},
}

# Venue mapping
venue_map = {
    'WSH': 'Nationals Park',
    'SD': 'Petco Park',
    'MIN': 'Target Field',
    'ARI': 'Chase Field',
    'SEA': 'T-Mobile Park',
    'MIL': 'Miller Park',
    'HOU': 'Minute Maid Park',
    'LAA': 'Angel Stadium',
}

# Create manual entries
manual_entries = []
start_id = 60000

for idx, (game_pk, away_abbr, home_abbr, away_score, home_score, game_date) in enumerate(missing_games):
    # Find the game in MLB boxscores
    game_row = boxscores_df[boxscores_df['game_pk'] == game_pk]
    
    if len(game_row) == 0:
        print(f"WARNING: Game {game_pk} not found in MLB boxscores!")
        continue
    
    game_row = game_row.iloc[0]
    
    # Extract venue from MLB data
    venue = game_row.get('venue_name', venue_map.get(home_abbr, ''))
    
    # Get team info
    away_info = team_info[away_abbr]
    home_info = team_info[home_abbr]
    
    # Create entry in BDL format
    entry = {
        'id': start_id + idx,
        'season': 2011,
        'date': f"{game_date}T00:00:00.000Z",  # Use midnight UTC for manual entries
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
manual_df.to_csv('manual_entries_2011.csv', index=False)
print(f"\nCreated {len(manual_entries)} manual entries")
print(f"Saved to manual_entries_2011.csv")
