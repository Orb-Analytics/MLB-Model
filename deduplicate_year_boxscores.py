import pandas as pd
import os
import sys
from pathlib import Path
import shutil
from datetime import datetime
from collections import defaultdict

# Generic script to deduplicate any year
if len(sys.argv) != 2:
    print("Usage: python deduplicate_year_boxscores.py <year>")
    print("Example: python deduplicate_year_boxscores.py 2013")
    sys.exit(1)

year = int(sys.argv[1])

# Expected game count (2020 was COVID-shortened season)
expected_games = 900 if year == 2020 else 2430
expected_per_team = 60 if year == 2020 else 162

# Paths
boxscore_dir = Path(f'data/{year}_data/mlb_data/raw/boxscores')
pitcher_dir = Path(f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores')
backup_dir = Path(f'data/{year}_data/mlb_data/raw/backup_before_deduplication_{datetime.now().strftime("%Y%m%d_%H%M%S")}')

# Create backup
print(f"\n{'='*80}")
print(f"CREATING BACKUP FOR {year}")
print(f"{'='*80}")

backup_dir.mkdir(parents=True, exist_ok=True)

# Backup boxscores
backup_boxscore_dir = backup_dir / 'boxscores'
backup_boxscore_dir.mkdir(exist_ok=True)
for file in boxscore_dir.glob('*.csv'):
    shutil.copy2(file, backup_boxscore_dir / file.name)
    
# Backup pitcher boxscores
backup_pitcher_dir = backup_dir / 'starting_pitcher_boxscores'
backup_pitcher_dir.mkdir(exist_ok=True)
for file in pitcher_dir.glob('*.csv'):
    shutil.copy2(file, backup_pitcher_dir / file.name)

print(f"✅ Backup created at: {backup_dir}")

# Load all boxscores
print(f"\n{'='*80}")
print(f"LOADING BOXSCORES FOR {year}")
print(f"{'='*80}")

all_boxscores = []
for file in sorted(boxscore_dir.glob('*.csv')):
    df = pd.read_csv(file)
    all_boxscores.append(df)
    
boxscores = pd.concat(all_boxscores, ignore_index=True)
print(f"Total games loaded: {len(boxscores)}")

# Find duplicates by game_pk
print(f"\n{'='*80}")
print(f"FINDING DUPLICATE GAME_PKS")
print(f"{'='*80}")

duplicate_game_pks = boxscores[boxscores.duplicated(subset=['game_pk'], keep=False)].sort_values('game_pk')
unique_duplicate_pks = duplicate_game_pks['game_pk'].unique()

print(f"Found {len(unique_duplicate_pks)} game_pks with duplicates (showing first 10):")
for i, game_pk in enumerate(unique_duplicate_pks[:10]):
    dupes = duplicate_game_pks[duplicate_game_pks['game_pk'] == game_pk][['game_pk', 'date', 'away_team_abbreviation', 'home_team_abbreviation']]
    print(f"\ngame_pk {game_pk}:")
    for _, row in dupes.iterrows():
        print(f"  {row['date']}: {row['away_team_abbreviation']} @ {row['home_team_abbreviation']}")

if len(unique_duplicate_pks) > 10:
    print(f"\n... and {len(unique_duplicate_pks) - 10} more duplicates")

# Deduplicate - keep the LAST occurrence (latest date = when game was actually played)
print(f"\n{'='*80}")
print(f"DEDUPLICATING BOXSCORES")
print(f"{'='*80}")

boxscores_sorted = boxscores.sort_values(['game_pk', 'date'])
boxscores_deduped = boxscores_sorted.drop_duplicates(subset=['game_pk'], keep='last')

print(f"Before deduplication: {len(boxscores)} games")
print(f"After deduplication: {len(boxscores_deduped)} games")
print(f"Removed: {len(boxscores) - len(boxscores_deduped)} duplicate entries")

# Load all pitcher boxscores
print(f"\n{'='*80}")
print(f"LOADING PITCHER BOXSCORES FOR {year}")
print(f"{'='*80}")

all_pitchers = []
for file in sorted(pitcher_dir.glob('*.csv')):
    df = pd.read_csv(file)
    all_pitchers.append(df)
    
pitchers = pd.concat(all_pitchers, ignore_index=True)
print(f"Total pitcher records loaded: {len(pitchers)}")

# Deduplicate pitcher boxscores by game_pk (keep last)
print(f"\n{'='*80}")
print(f"DEDUPLICATING PITCHER BOXSCORES")
print(f"{'='*80}")

pitchers_sorted = pitchers.sort_values(['game_pk', 'date'])
pitchers_deduped = pitchers_sorted.drop_duplicates(subset=['game_pk'], keep='last')

print(f"Before deduplication: {len(pitchers)} pitcher records")
print(f"After deduplication: {len(pitchers_deduped)} pitcher records")
print(f"Removed: {len(pitchers) - len(pitchers_deduped)} duplicate entries")

# Write deduplicated boxscores back to files
print(f"\n{'='*80}")
print(f"WRITING DEDUPLICATED BOXSCORES")
print(f"{'='*80}")

for date, group in boxscores_deduped.groupby('date'):
    file_path = boxscore_dir / f'boxscores_{date}.csv'
    group.to_csv(file_path, index=False)

print(f"✅ Wrote {len(boxscores_deduped)} games across {boxscores_deduped['date'].nunique()} dates")

# Write deduplicated pitcher boxscores back to files
print(f"\n{'='*80}")
print(f"WRITING DEDUPLICATED PITCHER BOXSCORES")
print(f"{'='*80}")

for date, group in pitchers_deduped.groupby('date'):
    file_path = pitcher_dir / f'starting_pitcher_boxscores_{date}.csv'
    group.to_csv(file_path, index=False)

print(f"✅ Wrote {len(pitchers_deduped)} pitcher records across {pitchers_deduped['date'].nunique()} dates")

# Verify final counts
print(f"\n{'='*80}")
print(f"VERIFICATION")
print(f"{'='*80}")

# Reload and count
all_boxscores_after = []
for file in sorted(boxscore_dir.glob('*.csv')):
    df = pd.read_csv(file)
    all_boxscores_after.append(df)
    
final_boxscores = pd.concat(all_boxscores_after, ignore_index=True)
final_unique_game_pks = final_boxscores['game_pk'].nunique()

print(f"Final boxscore count: {len(final_boxscores)} games (expected: {expected_games})")
print(f"Unique game_pks: {final_unique_game_pks}")

# Verify team game counts
print(f"\n{'='*80}")
print(f"VERIFYING TEAM GAME COUNTS (Expected: {expected_per_team} games per team)")
print(f"{'='*80}")

team_games = defaultdict(int)
for _, row in final_boxscores.iterrows():
    team_games[row['home_team_abbreviation']] += 1
    team_games[row['away_team_abbreviation']] += 1

teams_sorted = sorted(team_games.items(), key=lambda x: x[0])
all_correct = True

for team, count in teams_sorted:
    status = "✅" if count == expected_per_team else "❌"
    print(f"{status} {team:4s}: {count:3d} games")
    if count != expected_per_team:
        all_correct = False

print(f"\nTotal teams: {len(team_games)}")

if len(final_boxscores) == expected_games and len(team_games) == 30 and all_correct:
    print(f"\n✅ SUCCESS! {expected_games} games with all 30 teams playing exactly {expected_per_team} games!")
else:
    print(f"\n⚠️ Issues:")
    if len(final_boxscores) != expected_games:
        print(f"  • Expected {expected_games} games, got {len(final_boxscores)}")
    if len(team_games) != 30:
        print(f"  • Expected 30 teams, got {len(team_games)}")
    if not all_correct:
        print(f"  • Not all teams have {expected_per_team} games")
        for team, count in teams_sorted:
            if count != expected_per_team:
                diff = count - expected_per_team
                print(f"    - {team}: {count} games ({diff:+d})")

print(f"\n{'='*80}")
print(f"BACKUP LOCATION")
print(f"{'='*80}")
print(f"Original data backed up to: {backup_dir}")
