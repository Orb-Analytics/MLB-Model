import pandas as pd
import glob
from collections import Counter

print("="*70)
print("Identifying missing 2012 games")
print("="*70)

# Read all MLB boxscores
all_boxscores = []
for file in sorted(glob.glob('data/2012_data/mlb_data/raw/boxscores/*.csv')):
    df = pd.read_csv(file)
    all_boxscores.append(df)

boxscores_df = pd.concat(all_boxscores, ignore_index=True)
print(f"Total MLB boxscores: {len(boxscores_df)}")
print(f"Game_pk range: {boxscores_df['game_pk'].min()} to {boxscores_df['game_pk'].max()}")

# Read all BDL outlook
all_outlook = []
for file in sorted(glob.glob('data/2012_data/mlb_data/raw/bdl_data/game_outlook/*.csv')):
    df = pd.read_csv(file)
    all_outlook.append(df)

outlook_df = pd.concat(all_outlook, ignore_index=True)
print(f"Total BDL outlook: {len(outlook_df)}")

# Team abbreviation mapping
abbr_map = {
    'AZ': 'ARI',
    'ARI': 'ARI',
    'CWS': 'CHW',
    'CHW': 'CHW',
    'FLA': 'MIA',
    'MIA': 'MIA',
}

def normalize_abbr(abbr):
    return abbr_map.get(abbr, abbr)

# Normalize abbreviations
boxscores_df['away_norm'] = boxscores_df['away_team_abbreviation'].apply(normalize_abbr)
boxscores_df['home_norm'] = boxscores_df['home_team_abbreviation'].apply(normalize_abbr)
outlook_df['away_norm'] = outlook_df['away_team_abbreviation'].apply(normalize_abbr)
outlook_df['home_norm'] = outlook_df['home_team_abbreviation'].apply(normalize_abbr)

# Create match keys (teams + scores)
boxscores_df['match_key'] = (
    boxscores_df['away_norm'] + '|' +
    boxscores_df['home_norm'] + '|' +
    boxscores_df['away_batting_r'].astype(str) + '-' +
    boxscores_df['home_batting_r'].astype(str)
)

outlook_df['match_key'] = (
    outlook_df['away_norm'] + '|' +
    outlook_df['home_norm'] + '|' +
    outlook_df['away_team_score'].astype(str) + '-' +
    outlook_df['home_team_score'].astype(str)
)

# Count occurrences
boxscore_counts = Counter(boxscores_df['match_key'])
outlook_counts = Counter(outlook_df['match_key'])

# Find missing games
missing = []
for key, count in boxscore_counts.items():
    outlook_count = outlook_counts.get(key, 0)
    if count > outlook_count:
        diff = count - outlook_count
        for _ in range(diff):
            missing.append(key)

print(f"\n{'='*70}")
print(f"Found {len(missing)} missing game matchups in BDL outlook:")
print("="*70)

for key in missing:
    # Find the game details from boxscore
    games = boxscores_df[boxscores_df['match_key'] == key]
    for idx, game in games.iterrows():
        game_pk = game['game_pk']
        date = game['date']
        away = game['away_team_abbreviation']
        home = game['home_team_abbreviation']
        score = f"{int(game['away_batting_r'])}-{int(game['home_batting_r'])}"
        
        # Check if this specific game_pk is in outlook
        in_outlook = game_pk in outlook_df.get('game_pk', pd.Series()).values if 'game_pk' in outlook_df.columns else False
        
        if not in_outlook:
            print(f"\n  game_pk: {game_pk}")
            print(f"  Date: {date}")
            print(f"  Matchup: {away} @ {home}")
            print(f"  Score: {score}")
            print(f"  Match key: {key}")

print("\n" + "="*70)
