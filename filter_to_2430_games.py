import pandas as pd
import glob
import os

print("="*80)
print("FILTERING ALL DATASETS TO 2430 GAMES")
print("="*80)

# Load the list of games to keep (with their dates to handle duplicates)
keep_df = pd.read_csv('games_to_keep_2430.csv')
# Create a set of (date, game_pk) tuples to handle duplicates correctly
games_to_keep = set(zip(keep_df['date'], keep_df['game_pk']))
print(f"\nGames to keep: {len(games_to_keep)} date-game_pk pairs")

# Create backups
print("\nCreating backups...")
os.system('mkdir -p data/2009_data/mlb_data/raw/boxscores/backup_2467_games')
os.system('mkdir -p data/2009_data/mlb_data/raw/starting_pitcher_boxscores/backup_2467_games')
os.system('mkdir -p data/2009_data/mlb_data/raw/bdl_data/game_outlook/backup_2467_games')

os.system('cp data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv data/2009_data/mlb_data/raw/boxscores/backup_2467_games/')
os.system('cp data/2009_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_*.csv data/2009_data/mlb_data/raw/starting_pitcher_boxscores/backup_2467_games/')
os.system('cp data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv data/2009_data/mlb_data/raw/bdl_data/game_outlook/backup_2467_games/')
print("  Backups created")

# Step 1: Filter boxscore files
print("\nStep 1: Filtering boxscore files...")
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
total_before = 0
total_after = 0
dates_removed = []

for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    before_count = len(df)
    total_before += before_count
    
    # Filter to only games we want to keep (using date + game_pk pair)
    df['_keep_flag'] = df['game_pk'].apply(lambda pk: (date, pk) in games_to_keep)
    df_filtered = df[df['_keep_flag']].drop('_keep_flag', axis=1).reset_index(drop=True)
    after_count = len(df_filtered)
    total_after += after_count
    
    if before_count != after_count:
        removed = before_count - after_count
        dates_removed.append(f"{date}: {before_count} -> {after_count} (-{removed})")
    
    # Save filtered file
    df_filtered.to_csv(file, index=False)

print(f"  Before: {total_before} games")
print(f"  After: {total_after} games")
print(f"  Removed: {total_before - total_after} games")
if dates_removed:
    print(f"\n  Dates with games removed:")
    for msg in dates_removed[:10]:
        print(f"    {msg}")
    if len(dates_removed) > 10:
        print(f"    ... and {len(dates_removed) - 10} more")

# Step 2: Filter starting pitcher boxscore files
print("\nStep 2: Filtering starting pitcher boxscore files...")
pitcher_files = sorted(glob.glob('data/2009_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_*.csv'))
total_before = 0
total_after = 0

for file in pitcher_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    before_count = len(df)
    total_before += before_count
    
    # Filter to only games we want to keep (using date + game_pk pair)
    df['_keep_flag'] = df['game_pk'].apply(lambda pk: (date, pk) in games_to_keep)
    df_filtered = df[df['_keep_flag']].drop('_keep_flag', axis=1).reset_index(drop=True)
    after_count = len(df_filtered)
    total_after += after_count
    
    # Save filtered file
    df_filtered.to_csv(file, index=False)

print(f"  Before: {total_before} games")
print(f"  After: {total_after} games")
print(f"  Removed: {total_before - total_after} games")

# Step 3: Filter game outlook files
print("\nStep 3: Filtering game outlook files...")
outlook_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv'))
total_before = 0
total_after = 0

for file in outlook_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    before_count = len(df)
    total_before += before_count
    
    # Filter to only games we want to keep (using date + game_pk pair)
    df['_keep_flag'] = df['game_pk'].apply(lambda pk: (date, pk) in games_to_keep)
    df_filtered = df[df['_keep_flag']].drop('_keep_flag', axis=1).reset_index(drop=True)
    after_count = len(df_filtered)
    total_after += after_count
    
    # Save filtered file
    df_filtered.to_csv(file, index=False)

print(f"  Before: {total_before} games")
print(f"  After: {total_after} games")
print(f"  Removed: {total_before - total_after} games")

# Step 4: Final verification
print("\n" + "="*80)
print("FINAL VERIFICATION")
print("="*80)

box_count = sum(len(pd.read_csv(f)) for f in glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
pitch_count = sum(len(pd.read_csv(f)) for f in glob.glob('data/2009_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_*.csv'))
out_count = sum(len(pd.read_csv(f)) for f in glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv'))

print(f"\nFinal game counts:")
print(f"  Boxscores: {box_count}")
print(f"  Starting pitcher boxscores: {pitch_count}")
print(f"  Game outlook: {out_count}")

if box_count == pitch_count == out_count == 2430:
    print(f"\n✅ SUCCESS! All datasets filtered to exactly 2,430 games")
else:
    print(f"\n⚠️  WARNING: Counts don't match!")

print("="*80)
