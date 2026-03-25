#!/usr/bin/env python3
"""
Count games per team in 2011 BDL game outlook to identify missing games.
"""

import pandas as pd
import glob
from collections import defaultdict

# Load all game outlook files
files = glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv')
all_games = pd.concat([pd.read_csv(f) for f in files])

print(f"Total games in outlook: {len(all_games)}")
print(f"Expected for 30 teams * 162 games / 2: {30 * 162 / 2}")
print()

# Count games per team (both home and away)
team_games = defaultdict(int)

for _, row in all_games.iterrows():
    home_team = row['home_team_abbreviation']
    away_team = row['away_team_abbreviation']
    team_games[home_team] += 1
    team_games[away_team] += 1

# Sort by game count
sorted_teams = sorted(team_games.items(), key=lambda x: x[1])

print("=" * 60)
print("Games per team (sorted by count):")
print("=" * 60)

missing_games = []
for team, count in sorted_teams:
    status = ""
    if count < 162:
        status = f" ⚠️  MISSING {162 - count} games"
        missing_games.append((team, 162 - count))
    elif count > 162:
        status = f" ⚠️  EXTRA {count - 162} games"
    
    print(f"{team:5s}: {count:3d} games{status}")

print()
print("=" * 60)
print("Summary:")
print("=" * 60)
print(f"Teams with fewer than 162 games: {len([t for t, c in team_games.items() if c < 162])}")
print(f"Total missing games: {sum([162 - c for t, c in team_games.items() if c < 162])}")
print()

if missing_games:
    print("Teams missing games:")
    for team, missing in missing_games:
        print(f"  {team}: missing {missing} games")
