#!/usr/bin/env python3
"""
Find missing games in 2011 BDL game outlook by comparing to MLB boxscores.
"""

import pandas as pd
import glob
from collections import defaultdict

print("="*80)
print("Finding Missing Games in 2011 BDL Game Outlook")
print("="*80)

# Load MLB boxscores
print("\nLoading MLB boxscores...")
box_files = sorted(glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv'))
mlb_games = []

for f in box_files:
    df = pd.read_csv(f)
    for _, row in df.iterrows():
        mlb_games.append({
            'game_pk': row['game_pk'],
            'date': row['officialDate'],
            'home_team': row['home_abbreviation'],
            'away_team': row['away_abbreviation'],
            'home_score': row['home_score'],
            'away_score': row['away_score']
        })

mlb_df = pd.DataFrame(mlb_games)
print(f"MLB total games: {len(mlb_df)}")
print(f"Date range: {mlb_df['date'].min()} to {mlb_df['date'].max()}")

# Team abbreviation mapping (BDL to MLB)
bdl_to_mlb = {
    'AZ': 'ARI',
    'CWS': 'CHW',
    'FLA': 'MIA',
}

# Load BDL game outlook
print("\nLoading BDL game outlook...")
bdl_files = sorted(glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
bdl_games = []

for f in bdl_files:
    df = pd.read_csv(f)
    for _, row in df.iterrows():
        # Parse UTC date from the 'date' field
        date_str = str(row['date'])
        if 'T' in date_str:
            date_only = date_str.split('T')[0]
        else:
            date_only = date_str
        
        home_team = str(row['home_team_abbreviation'])
        away_team = str(row['away_team_abbreviation'])
        
        # Apply team mapping
        home_team = bdl_to_mlb.get(home_team, home_team)
        away_team = bdl_to_mlb.get(away_team, away_team)
        
        bdl_games.append({
            'bdl_id': row['id'],
            'date_utc': date_only,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': row['home_team_score'],
            'away_score': row['away_team_score']
        })

bdl_df = pd.DataFrame(bdl_games)
print(f"BDL total games: {len(bdl_df)}")
print(f"Date range (UTC): {bdl_df['date_utc'].min()} to {bdl_df['date_utc'].max()}")

# Create matching keys for comparison
# We'll try to match on teams and scores (ignoring date initially due to timezone issues)
print("\nMatching games by teams + scores...")

mlb_df['match_key'] = mlb_df['home_team'] + '_' + mlb_df['away_team'] + '_' + \
                      mlb_df['home_score'].astype(str) + '_' + mlb_df['away_score'].astype(str)

bdl_df['match_key'] = bdl_df['home_team'] + '_' + bdl_df['away_team'] + '_' + \
                      bdl_df['home_score'].astype(str) + '_' + bdl_df['away_score'].astype(str)

mlb_keys = set(mlb_df['match_key'])
bdl_keys = set(bdl_df['match_key'])

# Find games in MLB but not in BDL
missing_keys = mlb_keys - bdl_keys
print(f"\nGames in MLB but not in BDL (by team+score): {len(missing_keys)}")

if len(missing_keys) > 0:
    print("\n" + "="*80)
    print("MISSING GAMES:")
    print("="*80)
    
    missing_games = mlb_df[mlb_df['match_key'].isin(missing_keys)].sort_values('date')
    
    for idx, row in missing_games.iterrows():
        print(f"\nGame PK: {row['game_pk']}")
        print(f"  Date: {row['date']}")
        print(f"  Matchup: {row['away_team']} @ {row['home_team']}")
        print(f"  Score: {row['away_score']} - {row['home_score']}")
    
    # Save to CSV for reference
    missing_games.to_csv('missing_2011_games.csv', index=False)
    print(f"\n✅ Missing games saved to: missing_2011_games.csv")

# Also check for duplicates in BDL that might indicate matching issues
print("\n" + "="*80)
print("CHECKING FOR DUPLICATES:")
print("="*80)

bdl_dup = bdl_df[bdl_df.duplicated(subset=['match_key'], keep=False)]
if len(bdl_dup) > 0:
    print(f"⚠️  Found {len(bdl_dup)} duplicate matches in BDL data")
    print(bdl_dup[['date_utc', 'home_team', 'away_team', 'home_score', 'away_score']].to_string())
else:
    print("✅ No duplicates found in BDL data")

mlb_dup = mlb_df[mlb_df.duplicated(subset=['match_key'], keep=False)]
if len(mlb_dup) > 0:
    print(f"\n⚠️  Found {len(mlb_dup)} duplicate matches in MLB data (likely doubleheaders)")
    print(mlb_dup[['date', 'home_team', 'away_team', 'home_score', 'away_score', 'game_pk']].to_string())
else:
    print("✅ No duplicates found in MLB data")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"MLB games: {len(mlb_df)}")
print(f"BDL games: {len(bdl_df)}")
print(f"Missing from BDL: {len(missing_keys)}")
print("="*80)
