#!/usr/bin/env python3
"""
Match fetched BDL games with the 8 missing MLB boxscore games.
"""

import pandas as pd

# Load fetched BDL games
bdl_fetched = pd.read_csv('fetched_missing_2011_games.csv')

# Load MLB boxscores for these dates
mlb_boxscores = pd.read_csv('data/2011_data/mlb_data/raw/boxscores/boxscores_2011-09-08.csv')
mlb_boxscores2 = pd.read_csv('data/2011_data/mlb_data/raw/boxscores/boxscores_2011-09-28.csv')
mlb_boxscores = pd.concat([mlb_boxscores, mlb_boxscores2])

mlb_boxscores['home_score'] = mlb_boxscores['home_batting_r']
mlb_boxscores['away_score'] = mlb_boxscores['away_batting_r']

# The 8 specific missing game_pks
MISSING_GAME_PKS = [289037, 289311, 289315, 289316, 289318, 289320, 289321, 289322]

# Filter to just the missing games
missing_mlb = mlb_boxscores[mlb_boxscores['game_pk'].isin(MISSING_GAME_PKS)].copy()

print("=" * 80)
print("The 8 Missing MLB Games:")
print("=" * 80)
print(missing_mlb[['game_pk', 'date', 'away_team_abbreviation', 'home_team_abbreviation', 
                    'away_score', 'home_score']])

# Team abbreviation normalization
def normalize_team(abbr):
    mapping = {'AZ': 'ARI', 'CWS': 'CHW', 'FLA': 'MIA'}
    return mapping.get(abbr, abbr)

# Extract date from BDL timestamp
bdl_fetched['date_only'] = pd.to_datetime(bdl_fetched['date']).dt.date.astype(str)

print("\n" + "=" * 80)
print("Matching with Fetched BDL Games:")
print("=" * 80)

matched_games = []

for _, mlb_game in missing_mlb.iterrows():
    mlb_date = mlb_game['date']
    mlb_home = normalize_team(mlb_game['home_team_abbreviation'])
    mlb_away = normalize_team(mlb_game['away_team_abbreviation'])
    
    # Find matching BDL game (by teams, scores might be missing in BDL)
    matches = bdl_fetched[
        (bdl_fetched['date_only'].str.contains(mlb_date.split('T')[0])) &
        (bdl_fetched['home_team_abbreviation'].apply(normalize_team) == mlb_home) &
        (bdl_fetched['away_team_abbreviation'].apply(normalize_team) == mlb_away)
    ]
    
    if len(matches) > 0:
        bdl_game = matches.iloc[0]
        print(f"\n✅ MATCH FOUND:")
        print(f"   MLB game_pk: {mlb_game['game_pk']}")
        print(f"   MLB: {mlb_away} @ {mlb_home} ({mlb_game['away_score']}-{mlb_game['home_score']}) on {mlb_date}")
        print(f"   BDL ID: {bdl_game['id']}")
        print(f"   BDL: {bdl_game['away_team_abbreviation']} @ {bdl_game['home_team_abbreviation']} on {bdl_game['date']}")
        
        # Add scores to BDL data
        matched_game = bdl_game.copy()
        matched_game['home_team_score'] = int(mlb_game['home_score'])
        matched_game['away_team_score'] = int(mlb_game['away_score'])
        matched_game['mlb_game_pk'] = mlb_game['game_pk']
        matched_games.append(matched_game)
    else:
        print(f"\n❌ NO MATCH:")
        print(f"   Looking for: {mlb_away} @ {mlb_home} on {mlb_date}")
        print(f"   Available BDL games on that date:")
        same_date = bdl_fetched[bdl_fetched['date_only'].str.contains(mlb_date.split('T')[0])]
        for _, g in same_date.iterrows():
            print(f"      {g['away_team_abbreviation']} @ {g['home_team_abbreviation']}")

print("\n" + "=" * 80)
print(f"Summary: Matched {len(matched_games)} of 8 missing games")
print("=" * 80)

if matched_games:
    matched_df = pd.DataFrame(matched_games)
    matched_df.to_csv('matched_missing_2011_games.csv', index=False)
    print(f"\n✅ Saved matched games with scores to: matched_missing_2011_games.csv")
    
    print("\nMatched games summary:")
    print(matched_df[['id', 'mlb_game_pk', 'date', 'home_team_abbreviation', 'away_team_abbreviation',
                      'home_team_score', 'away_team_score']])
