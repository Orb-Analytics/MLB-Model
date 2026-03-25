#!/usr/bin/env python3
"""
Identify the 8 specific missing games by comparing MLB and BDL matchup frequencies.
"""

import pandas as pd
import glob
from collections import Counter

# Load MLB boxscores
print("Loading MLB boxscores...")
mlb_files = glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv')
mlb_df = pd.concat([pd.read_csv(f) for f in mlb_files])

# Load BDL outlook (original restored data)
print("Loading BDL game outlook...")
bdl_files = glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv')
bdl_df = pd.concat([pd.read_csv(f) for f in bdl_files])

print(f"\nMLB boxscores: {len(mlb_df)} games")
print(f"BDL outlook: {len(bdl_df)} games")
print(f"Missing: {len(mlb_df) - len(bdl_df)} games\n")

# Team abbreviation normalization
def normalize_team(abbr):
    mapping = {'AZ': 'ARI', 'CWS': 'CHW', 'FLA': 'MIA'}
    return mapping.get(abbr, abbr)

# Create matchup keys (away @ home)
mlb_df['matchup'] = (
    mlb_df['away_team_abbreviation'].apply(normalize_team) + '@' +
    mlb_df['home_team_abbreviation'].apply(normalize_team)
)

bdl_df['matchup'] = (
    bdl_df['away_team_abbreviation'].apply(normalize_team) + '@' +
    bdl_df['home_team_abbreviation'].apply(normalize_team)
)

# Count matchup frequencies
mlb_matchups = Counter(mlb_df['matchup'])
bdl_matchups = Counter(bdl_df['matchup'])

# Find matchups that appear more times in MLB than in BDL
missing_matchups = []
for matchup, mlb_count in mlb_matchups.items():
    bdl_count = bdl_matchups.get(matchup, 0)
    if mlb_count > bdl_count:
        missing_matchups.append((matchup, mlb_count - bdl_count, mlb_count, bdl_count))

print("=" * 80)
print(f"Found {len(missing_matchups)} matchups with missing games")
print(f"Total missing games: {sum(m[1] for m in missing_matchups)}")
print("=" * 80)

if missing_matchups:
    print("\nMissing matchups (Away @ Home):")
    print("-" * 80)
    
    all_missing_games = []
    for matchup, missing_count, mlb_count, bdl_count in sorted(missing_matchups):
        away, home = matchup.split('@')
        print(f"\n{away} @ {home}")
        print(f"  In MLB: {mlb_count} game(s)")
        print(f"  In BDL: {bdl_count} game(s)")
        print(f"  Missing: {missing_count} game(s)")
        
        # Get the specific MLB games for this matchup
        mlb_games = mlb_df[mlb_df['matchup'] == matchup].sort_values('date')
        bdl_games = bdl_df[bdl_df['matchup'] == matchup].sort_values('date')
        
        print(f"  MLB game_pks: {mlb_games['game_pk'].tolist()}")
        print(f"  MLB dates: {mlb_games['date'].tolist()}")
        
        if len(bdl_games) > 0:
            print(f"  BDL has games on: {bdl_games['date'].str[:10].tolist()}")
        
        # For now, assume the missing games are the ones we need to fetch
        # We'll need to do more analysis to determine which specific games
        for _, game in mlb_games.head(missing_count).iterrows():
            all_missing_games.append({
                'game_pk': game['game_pk'],
                'date': game['date'],
                'away': away,
                'home': home,
                'away_score': int(game['away_batting_r']),
                'home_score': int(game['home_batting_r'])
            })
    
    print("\n" + "=" * 80)
    print("Detailed list of potentially missing games:")
    print("=" * 80)
    
    for i, game in enumerate(all_missing_games, 1):
        print(f"\n{i}. Game PK: {game['game_pk']}")
        print(f"   Date: {game['date']}")
        print(f"   Matchup: {game['away']} @ {game['home']}")
        print(f"   Score: {game['away_score']}-{game['home_score']}")
    
    # Save to CSV
    if all_missing_games:
        missing_df = pd.DataFrame(all_missing_games)
        missing_df.to_csv('identified_missing_2011_games.csv', index=False)
        print(f"\n✅ Saved to: identified_missing_2011_games.csv")
        print(f"\nTotal identified: {len(all_missing_games)} games")

print("\n" + "=" * 80)
print("Note: These matchups appear more times in MLB than BDL.")
print("The actual missing games need to be determined by excluding games")
print("already in BDL (accounting for UTC date differences).")
print("=" * 80)
