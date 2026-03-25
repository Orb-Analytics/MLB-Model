#!/usr/bin/env python3
"""
Find missing 2011 games by matching on teams + scores (ignoring dates due to UTC issue).
"""

import pandas as pd
import glob

# Load all MLB boxscores
print("Loading MLB boxscores...")
box_files = glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv')
boxscores = pd.concat([pd.read_csv(f) for f in box_files])
boxscores['home_score'] = boxscores['home_batting_r']
boxscores['away_score'] = boxscores['away_batting_r']

# Load all BDL game outlook
print("Loading BDL game outlook...")
bdl_files = glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv')
bdl_outlook = pd.concat([pd.read_csv(f) for f in bdl_files])

print(f"\nMLB boxscores: {len(boxscores)} games")
print(f"BDL outlook: {len(bdl_outlook)} games")
print(f"Difference: {len(boxscores) - len(bdl_outlook)} games\n")

# Team abbreviation mapping (BDL vs MLB)
team_mapping = {
    'AZ': 'ARI',
    'CWS': 'CHW',
    'FLA': 'MIA'
}

def normalize_team(abbr):
    return team_mapping.get(abbr, abbr)

# Create match key: teams + scores (no date)
boxscores['match_key'] = (
    boxscores['away_team_abbreviation'].apply(normalize_team) + '|' +
    boxscores['home_team_abbreviation'].apply(normalize_team) + '|' +
    boxscores['away_score'].astype(str) + '-' +
    boxscores['home_score'].astype(str)
)

bdl_outlook['match_key'] = (
    bdl_outlook['away_team_abbreviation'].apply(normalize_team) + '|' +
    bdl_outlook['home_team_abbreviation'].apply(normalize_team) + '|' +
    bdl_outlook['away_team_score'].astype(str) + '-' +
    bdl_outlook['home_team_score'].astype(str)
)

# Create a multiset counter for each dataset
from collections import Counter
box_keys = list(boxscores['match_key'])
bdl_keys = list(bdl_outlook['match_key'])

box_counter = Counter(box_keys)
bdl_counter = Counter(bdl_keys)

# Find games that appear more times in boxscores than in BDL
missing_matches = []
for key, box_count in box_counter.items():
    bdl_count = bdl_counter.get(key, 0)
    if box_count > bdl_count:
        diff = box_count - bdl_count
        missing_matches.append((key, diff, box_count, bdl_count))

print("=" * 80)
print(f"Found {len(missing_matches)} game matchups with missing games")
print(f"Total missing occurrences: {sum(m[1] for m in missing_matches)}")
print("=" * 80)

if missing_matches:
    print("\nMissing game matchups (team|team|score):")
    print("-" * 80)
    
    all_missing_games = []
    for match_key, missing_count, box_count, bdl_count in sorted(missing_matches):
        print(f"\n{match_key}")
        print(f"  In MLB boxscores: {box_count} occurrence(s)")
        print(f"  In BDL outlook: {bdl_count} occurrence(s)")
        print(f"  Missing: {missing_count} game(s)")
        
        # Get the specific games
        games = boxscores[boxscores['match_key'] == match_key].sort_values('date')
        print(f"  Game PKs: {games['game_pk'].tolist()}")
        print(f"  Dates: {games['date'].tolist()}")
        
        all_missing_games.extend(games['game_pk'].tolist()[:missing_count])
    
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Total missing games: {len(all_missing_games)}")
    print(f"Game PKs (may include duplicates if same matchup occurred multiple times):")
    print(sorted(set(all_missing_games)))
    
    # Save for reference
    missing_details = boxscores[boxscores['match_key'].isin([m[0] for m in missing_matches])][
        ['game_pk', 'date', 'home_team_abbreviation', 'away_team_abbreviation', 
         'home_score', 'away_score', 'home_team_display_name', 'away_team_display_name', 'match_key']
    ].sort_values(['match_key', 'date'])
    
    missing_details.to_csv('missing_2011_games_by_matchup.csv', index=False)
    print(f"\n✅ Saved details to: missing_2011_games_by_matchup.csv")
