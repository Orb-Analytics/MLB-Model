import pandas as pd
import os
from pathlib import Path
import shutil
from datetime import datetime

# Backup and deduplicate 2011 boxscores
year = 2011

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

print(f"Found {len(unique_duplicate_pks)} game_pks with duplicates:")
for game_pk in unique_duplicate_pks:
    dupes = duplicate_game_pks[duplicate_game_pks['game_pk'] == game_pk][['game_pk', 'date', 'away_team_abbreviation', 'home_team_abbreviation']]
    print(f"\ngame_pk {game_pk}:")
    for _, row in dupes.iterrows():
        print(f"  {row['date']}: {row['away_team_abbreviation']} @ {row['home_team_abbreviation']}")

# Deduplicate - keep the LAST occurrence (latest date = when game was actually played)
print(f"\n{'='*80}")
print(f"DEDUPLICATING BOXSCORES")
print(f"{'='*80}")

# Sort by game_pk and date, then keep last occurrence of each game_pk
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

# Group by date and write to respective files
for date, group in boxscores_deduped.groupby('date'):
    file_path = boxscore_dir / f'boxscores_{date}.csv'
    group.to_csv(file_path, index=False)
    print(f"✅ Wrote {len(group)} games to {file_path.name}")

# Write deduplicated pitcher boxscores back to files
print(f"\n{'='*80}")
print(f"WRITING DEDUPLICATED PITCHER BOXSCORES")
print(f"{'='*80}")

for date, group in pitchers_deduped.groupby('date'):
    file_path = pitcher_dir / f'starting_pitcher_boxscores_{date}.csv'
    group.to_csv(file_path, index=False)
    print(f"✅ Wrote {len(group)} pitcher records to {file_path.name}")

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

all_pitchers_after = []
for file in sorted(pitcher_dir.glob('*.csv')):
    df = pd.read_csv(file)
    all_pitchers_after.append(df)
    
final_pitchers = pd.concat(all_pitchers_after, ignore_index=True)

print(f"Final boxscore count: {len(final_boxscores)} games")
print(f"Unique game_pks: {final_unique_game_pks}")
print(f"Final pitcher count: {len(final_pitchers)} records")

if len(final_boxscores) == 2430:
    print(f"\n✅ SUCCESS! Reduced to exactly 2,430 games!")
else:
    print(f"\n⚠️ Final count is {len(final_boxscores)}, expected 2,430")

print(f"\n{'='*80}")
print(f"BACKUP LOCATION")
print(f"{'='*80}")
print(f"Original data backed up to: {backup_dir}")
