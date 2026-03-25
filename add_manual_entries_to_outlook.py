import pandas as pd
import os

# Read the manual entries
manual_entries = pd.read_csv('manual_entries_2011.csv')
print(f"Loaded {len(manual_entries)} manual entries")

# Group by date (extract date from timestamp)
manual_entries['date_only'] = pd.to_datetime(manual_entries['date']).dt.date

# Process each date
for date_only, group in manual_entries.groupby('date_only'):
    # Format the filename
    outlook_file = f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date_only}.csv'
    
    print(f"\nProcessing {date_only}...")
    
    # Read existing file if it exists
    if os.path.exists(outlook_file):
        existing_df = pd.read_csv(outlook_file)
        print(f"  Existing games: {len(existing_df)}")
        
        # Append manual entries
        combined_df = pd.concat([existing_df, group.drop('date_only', axis=1)], ignore_index=True)
        print(f"  After adding manual entries: {len(combined_df)}")
        
        # Save back
        combined_df.to_csv(outlook_file, index=False)
        print(f"  ✓ Updated {outlook_file}")
    else:
        # Create new file with just manual entries
        group.drop('date_only', axis=1).to_csv(outlook_file, index=False)
        print(f"  ✓ Created new {outlook_file}")

# Verify total count
import glob
total_games = 0
for file in glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/*.csv'):
    df = pd.read_csv(file)
    total_games += len(df)

print(f"\n{'='*60}")
print(f"Total games in BDL game outlook after adding manual entries: {total_games}")
print(f"Expected: 2430")
print(f"Match: {'✓' if total_games == 2430 else '✗'}")
