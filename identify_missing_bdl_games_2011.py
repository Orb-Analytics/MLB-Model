import pandas as pd
from pathlib import Path

year = 2011

# Team abbreviation mapping: ML B -> BDL
MLB_TO_BDL = {
    'AZ': 'ARI',
    'CWS': 'CHW',
    'FLA': 'MIA',
}

def normalize_team(team):
    """Convert MLB abbreviation to BDL abbreviation"""
    return MLB_TO_BDL.get(team, team)

# Load all MLB boxscores
boxscore_dir = Path(f'data/{year}_data/mlb_data/raw/boxscores')
all_boxscores = []
for file in sorted(boxscore_dir.glob('*.csv')):
    df = pd.read_csv(file)
    all_boxscores.append(df)
    
boxscores = pd.concat(all_boxscores, ignore_index=True)

# Load all BDL game outlook
bdl_dir = Path(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook')
all_bdl = []
for file in sorted(bdl_dir.glob('game_outlook_*.csv')):
    df = pd.read_csv(file)
    all_bdl.append(df)
    
bdl = pd.concat(all_bdl, ignore_index=True)

# Normalize BDL dates (remove timestamp, keep only date part)
bdl['date'] = pd.to_datetime(bdl['date']).dt.strftime('%Y-%m-%d')

print(f"\n{'='*80}")
print(f"IDENTIFYING MISSING GAMES FROM BDL ({year})")
print(f"{'='*80}")
print(f"MLB boxscores: {len(boxscores)} games")
print(f"BDL outlook: {len(bdl)} games")
print(f"Missing from BDL: {len(boxscores) - len(bdl)} games")

# Create matchup keys for comparison
# BDL uses "id" column, MLB uses "game_pk"
# We'll match by date + teams

def create_matchup_key(row, away_col, home_col, normalize=False):
    """Create a unique key for a game based on date and teams"""
    away = row[away_col]
    home = row[home_col]
    if normalize:
        away = normalize_team(away)
        home = normalize_team(home)
    return f"{row['date']}|{away}|{home}"

# Create keys for MLB games (normalize to BDL abbreviations)
mlb_keys = set()
mlb_game_lookup = {}
for _, row in boxscores.iterrows():
    key = create_matchup_key(row, 'away_team_abbreviation', 'home_team_abbreviation', normalize=True)
    mlb_keys.add(key)
    mlb_game_lookup[key] = row

# Create keys for BDL games (already in BDL format)
bdl_keys = set()
for _, row in bdl.iterrows():
    key = create_matchup_key(row, 'away_team_abbreviation', 'home_team_abbreviation', normalize=False)
    bdl_keys.add(key)

# Find missing games
missing_keys = mlb_keys - bdl_keys

print(f"\n{'='*80}")
print(f"MISSING GAMES DETAILS")
print(f"{'='*80}")

if missing_keys:
    missing_games = []
    for key in sorted(missing_keys):
        game = mlb_game_lookup[key]
        # Show both MLB and BDL abbreviations
        away_mlb = game['away_team_abbreviation']
        home_mlb = game['home_team_abbreviation']
        away_bdl = normalize_team(away_mlb)
        home_bdl = normalize_team(home_mlb)
        
        missing_games.append({
            'game_pk': game['game_pk'],
            'date': game['date'],
            'away_mlb': away_mlb,
            'home_mlb': home_mlb,
            'away_bdl': away_bdl,
            'home_bdl': home_bdl,
            'matchup': f"{away_bdl} @ {home_bdl}"
        })
        
    for i, game in enumerate(missing_games, 1):
        print(f"{i}. {game['date']}: {game['matchup']} (game_pk: {game['game_pk']})")
    
    # Save to CSV for reference
    missing_df = pd.DataFrame(missing_games)
    missing_df.to_csv(f'missing_bdl_games_{year}.csv', index=False)
    print(f"\n✅ Missing games saved to: missing_bdl_games_{year}.csv")
else:
    print("No missing games found!")

print(f"\n{'='*80}")
print(f"NEXT STEPS")
print(f"{'='*80}")
print(f"1. Fetch these {len(missing_keys)} games from BDL API")
print(f"2. Add them to the appropriate date files in game_outlook/")
