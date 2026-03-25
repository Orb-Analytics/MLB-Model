import pandas as pd
import os

print("="*70)
print("Adding manual entries to 2013 game outlook")
print("="*70)

# Read the manual entries
manual_entries = pd.read_csv('manual_entries_2013.csv')
print(f"Loaded {len(manual_entries)} manual entries")

# All entries are for the same date
date = '2013-10-03'
outlook_file = f'data/2013_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv'

if os.path.exists(outlook_file):
    existing_df = pd.read_csv(outlook_file)
    print(f"\nExisting games in {date}: {len(existing_df)}")
    
    # Append manual entries
    combined_df = pd.concat([existing_df, manual_entries], ignore_index=True)
    print(f"After adding manual entries: {len(combined_df)}")
    
    # Get the boxscore order for this date
    boxscore_file = f'data/2013_data/mlb_data/raw/boxscores/boxscores_{date}.csv'
    if os.path.exists(boxscore_file):
        boxscore_df = pd.read_csv(boxscore_file)
        boxscore_order = boxscore_df['game_pk'].tolist()
        
        print(f"\nReordering to match boxscore order...")
        print(f"Boxscore has {len(boxscore_order)} games")
        
        # Create mapping from game_pk to row
        game_dict = {int(row['game_pk']): row for _, row in combined_df.iterrows() if pd.notna(row['game_pk'])}
        
        # Reorder
        ordered_rows = []
        for game_pk in boxscore_order:
            if game_pk in game_dict:
                ordered_rows.append(game_dict[game_pk])
            else:
                print(f"  WARNING: game_pk {game_pk} not found in outlook")
        
        if len(ordered_rows) > 0:
            ordered_df = pd.DataFrame(ordered_rows)
            ordered_df.to_csv(outlook_file, index=False)
            print(f"\n✓ Updated and reordered {outlook_file}")
            print(f"  Final game count: {len(ordered_df)}")
else:
    print(f"\nOutlook file doesn't exist, creating new file...")
    # Need to reorder based on boxscore
    boxscore_file = f'data/2013_data/mlb_data/raw/boxscores/boxscores_{date}.csv'
    if os.path.exists(boxscore_file):
        boxscore_df = pd.read_csv(boxscore_file)
        boxscore_order = boxscore_df['game_pk'].tolist()
        
        game_dict = {int(row['game_pk']): row for _, row in manual_entries.iterrows()}
        ordered_rows = [game_dict[pk] for pk in boxscore_order if pk in game_dict]
        
        ordered_df = pd.DataFrame(ordered_rows)
        ordered_df.to_csv(outlook_file, index=False)
        print(f"✓ Created {outlook_file} with {len(ordered_df)} games")

# Verify final count
import glob
total_games = 0
for file in glob.glob('data/2013_data/mlb_data/raw/bdl_data/game_outlook/*.csv'):
    df = pd.read_csv(file)
    total_games += len(df)

print(f"\n{'='*70}")
print(f"Total games in BDL game outlook after adding manual entries: {total_games}")
print(f"Expected: 2430")
print(f"Match: {'✓' if total_games == 2430 else '✗'}")
print("="*70)
