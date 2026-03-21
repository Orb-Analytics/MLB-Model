#!/usr/bin/env python3
"""
Verify that each team appears exactly 162 times in the dataset
"""

import pandas as pd

print("="*80)
print("VERIFYING EACH TEAM HAS 162 GAMES")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset_with_duplicates.csv')
print(f"\nDataset: {len(df)} rows × {len(df.columns)} columns")

# Count home games per team
home_counts = df['home_team_abbreviation'].value_counts().sort_index()

# Count away games per team
away_counts = df['away_team_abbreviation'].value_counts().sort_index()

# Total games per team
all_teams = sorted(set(home_counts.index) | set(away_counts.index))
total_counts = {}

for team in all_teams:
    home = home_counts.get(team, 0)
    away = away_counts.get(team, 0)
    total = home + away
    total_counts[team] = {'home': home, 'away': away, 'total': total}

print(f"\nFound {len(all_teams)} teams")
print("\nGame counts per team:")
print(f"{'Team':<6} {'Home':>6} {'Away':>6} {'Total':>6}")
print("-" * 30)

teams_with_162 = 0
teams_with_issues = []

for team in sorted(all_teams):
    counts = total_counts[team]
    status = "✓" if counts['total'] == 162 else "✗"
    print(f"{team:<6} {counts['home']:>6} {counts['away']:>6} {counts['total']:>6} {status}")
    
    if counts['total'] == 162:
        teams_with_162 += 1
    else:
        teams_with_issues.append((team, counts['total']))

print("-" * 30)
print(f"\n✓ Teams with exactly 162 games: {teams_with_162}/{len(all_teams)}")

if teams_with_issues:
    print(f"\n❌ Teams with incorrect game counts:")
    for team, count in teams_with_issues:
        diff = count - 162
        print(f"  {team}: {count} games ({diff:+d})")
else:
    print("\n✓✓✓ ALL TEAMS HAVE EXACTLY 162 GAMES! ✓✓✓")

# Verify total games calculation
total_games = len(df)
expected_total = len(all_teams) * 162 / 2  # Divide by 2 because each game involves 2 teams
print(f"\nTotal games in dataset: {total_games}")
print(f"Expected (30 teams × 162 ÷ 2): {expected_total}")
print(f"Match: {'✓' if total_games == expected_total else '✗'}")

print("="*80)
