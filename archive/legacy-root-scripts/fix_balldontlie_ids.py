"""
Add balldontlie game IDs to box score files with proper team abbreviation mapping.
"""

import pandas as pd
import glob
import os

# Paths
BOXSCORE_DIR = "data/bdl_data/boxscores"
GAME_OUTLOOK_DIR = "data/bdl_data/game_outlook"

# Team abbreviation mapping: MLB -> Balldontlie
TEAM_ABB_MAPPING = {
    'AZ': 'ARI',    # Arizona Diamondbacks
    'CWS': 'CHW',   # Chicago White Sox
    'ATH': 'OAK',   # Oakland Athletics
}

print("=" * 80)
print("Adding Balldontlie Game IDs with Corrected Team Abbreviations")
print("=" * 80)
print()
print("Team abbreviation mappings:")
for mlb_abb, bdl_abb in TEAM_ABB_MAPPING.items():
    print(f"  {mlb_abb} (MLB) -> {bdl_abb} (Balldontlie)")
print()

# Load all game_outlook files
print("📋 Loading game_outlook files...")
game_outlook_files = sorted(glob.glob(f"{GAME_OUTLOOK_DIR}/game_outlook_2025-*.csv"))
all_outlooks = []
for f in game_outlook_files:
    df = pd.read_csv(f)
    all_outlooks.append(df)

game_outlook_df = pd.concat(all_outlooks, ignore_index=True)
print(f"✅ Loaded {len(game_outlook_df)} games from game_outlook")

# Clean up date format
game_outlook_df['date_clean'] = pd.to_datetime(game_outlook_df['date']).dt.date

print()
print("=" * 80)
print("Processing Box Score Files")
print("=" * 80)

# Create lookup dictionary
outlook_lookup = {}
for _, row in game_outlook_df.iterrows():
    key = (row['date_clean'], row['home_team_abbreviation'], row['away_team_abbreviation'])
    if key in outlook_lookup:
        if not isinstance(outlook_lookup[key], list):
            outlook_lookup[key] = [outlook_lookup[key]]
        outlook_lookup[key].append(row['id'])
    else:
        outlook_lookup[key] = row['id']

print(f"Created lookup table with {len(outlook_lookup)} unique matchups")
print()

# Process each box score file
boxscore_files = sorted(glob.glob(f"{BOXSCORE_DIR}/boxscores_2025-*.csv"))

matched_count = 0
unmatched_count = 0
total_count = 0
processed_files = 0
mapping_fixes = 0

for boxscore_file in boxscore_files:
    df = pd.read_csv(boxscore_file)
    total_count += len(df)
    
    # Clean up date format
    df['date_clean'] = pd.to_datetime(df['date']).dt.date
    
    # Map team abbreviations from MLB to Balldontlie format
    df['home_team_abb_mapped'] = df['home_team_abbreviation'].map(lambda x: TEAM_ABB_MAPPING.get(x, x))
    df['away_team_abb_mapped'] = df['away_team_abbreviation'].map(lambda x: TEAM_ABB_MAPPING.get(x, x))
    
    # Track how many needed mapping
    mapping_fixes += (df['home_team_abbreviation'] != df['home_team_abb_mapped']).sum()
    mapping_fixes += (df['away_team_abbreviation'] != df['away_team_abb_mapped']).sum()
    
    # Match using mapped abbreviations
    balldontlie_ids = []
    for _, row in df.iterrows():
        key = (row['date_clean'], row['home_team_abb_mapped'], row['away_team_abb_mapped'])
        
        if key in outlook_lookup:
            bdl_id = outlook_lookup[key]
            if isinstance(bdl_id, list):
                balldontlie_ids.append(bdl_id[0])
            else:
                balldontlie_ids.append(bdl_id)
            matched_count += 1
        else:
            balldontlie_ids.append(None)
            unmatched_count += 1
    
    df['balldontlie_game_id'] = balldontlie_ids
    
    # Drop temporary columns
    df = df.drop(['date_clean', 'home_team_abb_mapped', 'away_team_abb_mapped'], axis=1)
    
    # Reorder columns
    cols = df.columns.tolist()
    cols.remove('balldontlie_game_id')
    cols = ['balldontlie_game_id'] + cols
    df = df[cols]
    
    # Save
    df.to_csv(boxscore_file, index=False)
    processed_files += 1
    
    if processed_files <= 5 or processed_files % 50 == 0:
        date = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
        print(f"✅ Processed {date}: {len(df)} game(s)")

print()
print("=" * 80)
print("Summary")
print("=" * 80)
print(f"Total files processed:           {processed_files}")
print(f"Total games:                     {total_count}")
print(f"Team abbreviations mapped:       {mapping_fixes}")
print(f"Matched with balldontlie:        {matched_count}")
print(f"No balldontlie match:            {unmatched_count}")
print(f"Match rate:                      {matched_count/total_count*100:.1f}%")

print()
print("=" * 80)
print("Verification")
print("=" * 80)

sample_file = f"{BOXSCORE_DIR}/boxscores_2025-06-11.csv"
sample_df = pd.read_csv(sample_file)
print(f"Sample file: {sample_file}")
print(f"Total games: {len(sample_df)}")
print()

# Show Arizona game that should now match
az_game = sample_df[sample_df['home_team_abbreviation'] == 'AZ']
if len(az_game) > 0:
    print("Arizona game (previously unmatched):")
    row = az_game.iloc[0]
    print(f"  balldontlie_game_id: {row['balldontlie_game_id']}")
    print(f"  {row['away_team_abbreviation']} @ {row['home_team_abbreviation']}")
    print(f"  MLB uses 'AZ', balldontlie uses 'ARI' - now {'MATCHED ✅' if pd.notna(row['balldontlie_game_id']) else 'STILL UNMATCHED ❌'}")

print()
print("=" * 80)
print("✅ COMPLETE - All games retained with corrected matching!")
print("=" * 80)
