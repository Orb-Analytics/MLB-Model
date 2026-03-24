import pandas as pd
from pathlib import Path
from collections import defaultdict

year = 2011

# Load all boxscores
boxscore_dir = Path(f'data/{year}_data/mlb_data/raw/boxscores')
all_boxscores = []
for file in sorted(boxscore_dir.glob('*.csv')):
    df = pd.read_csv(file)
    all_boxscores.append(df)
    
boxscores = pd.concat(all_boxscores, ignore_index=True)

print(f"\n{'='*80}")
print(f"TEAM GAME COUNT VERIFICATION FOR {year}")
print(f"{'='*80}")
print(f"Total games: {len(boxscores)}")
print(f"Expected: 2,430 games (30 teams × 162 games / 2)")

# Count games per team
team_games = defaultdict(int)

for _, row in boxscores.iterrows():
    home_team = row['home_team_abbreviation']
    away_team = row['away_team_abbreviation']
    team_games[home_team] += 1
    team_games[away_team] += 1

print(f"\n{'='*80}")
print(f"GAMES PER TEAM")
print(f"{'='*80}")

teams_sorted = sorted(team_games.items(), key=lambda x: x[0])
all_162 = True

for team, count in teams_sorted:
    status = "✅" if count == 162 else "❌"
    print(f"{status} {team:4s}: {count:3d} games")
    if count != 162:
        all_162 = False

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"Total teams: {len(team_games)}")
print(f"Expected teams: 30")

if len(team_games) == 30 and all_162:
    print(f"\n✅ PERFECT! All 30 teams have exactly 162 games!")
    print(f"✅ Total: {len(boxscores)} games = (30 teams × 162 games) / 2")
else:
    print(f"\n⚠️ Issues found:")
    if len(team_games) != 30:
        print(f"  • Expected 30 teams, found {len(team_games)}")
    if not all_162:
        print(f"  • Not all teams have 162 games")
        for team, count in teams_sorted:
            if count != 162:
                diff = count - 162
                print(f"    - {team}: {count} games ({diff:+d})")
