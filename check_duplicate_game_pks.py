import pandas as pd
import glob
from collections import Counter

print("="*80)
print("CHECKING FOR DUPLICATE GAME_PKS IN THE 37 GAMES TO REMOVE")
print("="*80)

# Load the list of games to remove
remove_df = pd.read_csv('games_to_remove_37.csv')
games_to_remove = remove_df['game_pk'].values
print(f"\nGames to remove: {len(games_to_remove)}")
print(f"Unique game_pks: {len(set(games_to_remove))}")

if len(games_to_remove) != len(set(games_to_remove)):
    print(f"⚠️  WARNING: Found {len(games_to_remove) - len(set(games_to_remove))} duplicate game_pks in remove list!")
    duplicates = [pk for pk, count in Counter(games_to_remove).items() if count > 1]
    for pk in duplicates:
        print(f"  game_pk {pk} appears {Counter(games_to_remove)[pk]} times")
else:
    print("✅ No duplicates in the remove list")

# Check if any of these game_pks appear multiple times in the boxscore data
print("\nChecking for duplicates across all boxscore files...")
all_game_pks = []
game_pk_locations = {}  # game_pk -> list of (date, position)

boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    
    for idx, row in df.iterrows():
        game_pk = int(row['game_pk'])
        all_game_pks.append(game_pk)
        
        if game_pk not in game_pk_locations:
            game_pk_locations[game_pk] = []
        game_pk_locations[game_pk].append((date, idx))

print(f"  Total games in boxscore: {len(all_game_pks)}")
print(f"  Unique game_pks: {len(set(all_game_pks))}")

# Find duplicates
duplicates_in_boxscore = {pk: locs for pk, locs in game_pk_locations.items() if len(locs) > 1}

if duplicates_in_boxscore:
    print(f"\n⚠️  Found {len(duplicates_in_boxscore)} game_pks that appear multiple times in boxscore data:")
    for pk, locs in sorted(duplicates_in_boxscore.items()):
        print(f"  game_pk {pk} appears {len(locs)} times:")
        for date, pos in locs:
            print(f"    - {date} position {pos}")
else:
    print("\n✅ No duplicate game_pks in boxscore data")

# Check if any of the 37 games to remove have duplicates
print("\nChecking if any of the 37 games to remove are duplicates...")
remove_set = set(games_to_remove)
duplicates_in_remove_list = [pk for pk in remove_set if pk in duplicates_in_boxscore]

if duplicates_in_remove_list:
    print(f"⚠️  {len(duplicates_in_remove_list)} of the 37 games to remove have duplicate game_pks:")
    for pk in duplicates_in_remove_list:
        locs = game_pk_locations[pk]
        print(f"  game_pk {pk} appears at:")
        for date, pos in locs:
            in_remove = remove_df[remove_df['game_pk'] == pk]
            if len(in_remove) > 0 and in_remove.iloc[0]['date'] == date:
                print(f"    - {date} position {pos} [TO REMOVE]")
            else:
                print(f"    - {date} position {pos} [TO KEEP]")
else:
    print("✅ None of the 37 games to remove are duplicates")

print("="*80)
