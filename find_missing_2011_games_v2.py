#!/usr/bin/env python3
"""
Find which specific games are missing from 2011 BDL data by comparing with MLB boxscores.
"""

import pandas as pd
import glob

# Load all MLB boxscores
print("Loading MLB boxscores...")
box_files = glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv')
boxscores = pd.concat([pd.read_csv(f) for f in box_files])

# Load all BDL game outlook
print("Loading BDL game outlook...")
bdl_files = glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv')
bdl_outlook = pd.concat([pd.read_csv(f) for f in bdl_files])

print(f"\nMLB boxscores: {len(boxscores)} games")
print(f"BDL outlook: {len(bdl_outlook)} games")
print(f"Missing: {len(boxscores) - len(bdl_outlook)} games\n")

# Get all game_pks from boxscores
box_game_pks = set(boxscores['game_pk'].tolist())

print(f"Unique game_pks in boxscores: {len(box_game_pks)}")

# Since BDL doesn't have game_pk yet, let's create match keys based on teams and scores
# Get home_score and away_score from boxscores
boxscores['home_score'] = boxscores['home_batting_r']
boxscores['away_score'] = boxscores['away_batting_r']

# Create match keys
boxscores['match_key'] = (
    boxscores['date'] + '|' + 
    boxscores['home_team_abbreviation'] + '|' + 
    boxscores['away_team_abbreviation'] + '|' + 
    boxscores['home_score'].astype(str) + '|' + 
    boxscores['away_score'].astype(str)
)

bdl_outlook['match_key'] = (
    bdl_outlook['date'].str[:10] + '|' + 
    bdl_outlook['home_team_abbreviation'] + '|' + 
    bdl_outlook['away_team_abbreviation'] + '|' + 
    bdl_outlook['home_team_score'].astype(str) + '|' + 
    bdl_outlook['away_team_score'].astype(str)
)

# Find games in boxscores but not in BDL
box_keys = set(boxscores['match_key'])
bdl_keys = set(bdl_outlook['match_key'])

missing_keys = box_keys - bdl_keys

print("=" * 80)
print(f"Found {len(missing_keys)} missing game matchups")
print("=" * 80)

if missing_keys:
    # Get full details of missing games
    missing_games = boxscores[boxscores['match_key'].isin(missing_keys)].sort_values('date')
    
    print("\nMissing games details:")
    print("-" * 80)
    for idx, game in missing_games.iterrows():
        print(f"\nGame PK: {game['game_pk']}")
        print(f"Date: {game['date']}")
        print(f"Matchup: {game['away_team_abbreviation']} @ {game['home_team_abbreviation']}")
        print(f"Score: {game['away_score']} - {game['home_score']}")
        print(f"Teams: {game['away_team_display_name']} @ {game['home_team_display_name']}")

    print("\n" + "=" * 80)
    print("Summary of missing games:")
    print("=" * 80)
    
    # Save to CSV for reference
    missing_games_export = missing_games[[
        'game_pk', 'date', 'home_team_abbreviation', 'away_team_abbreviation', 
        'home_score', 'away_score', 'home_team_display_name', 'away_team_display_name'
    ]].copy()
    
    missing_games_export.to_csv('missing_2011_games_list.csv', index=False)
    print(f"\n✅ Saved missing games to: missing_2011_games_list.csv")
    print(f"\nGame PKs to fetch: {sorted(missing_games['game_pk'].tolist())}")
