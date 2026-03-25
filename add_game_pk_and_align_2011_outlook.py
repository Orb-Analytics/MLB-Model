import pandas as pd
import glob
import os
from datetime import datetime

# Team abbreviation mapping
abbr_map = {
    'AZ': 'ARI',
    'ARI': 'ARI',
    'CWS': 'CHW',
    'CHW': 'CHW',
    'FLA': 'MIA',
    'MIA': 'MIA',
}

def normalize_abbr(abbr):
    """Normalize team abbreviations"""
    return abbr_map.get(abbr, abbr)

print("="*60)
print("STEP 1: Loading MLB boxscores and creating lookup")
print("="*60)

# Read all MLB boxscores
all_boxscores = []
for file in sorted(glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv')):
    df = pd.read_csv(file)
    all_boxscores.append(df)

boxscores_df = pd.concat(all_boxscores, ignore_index=True)
print(f"Total MLB boxscores: {len(boxscores_df)}")

# Normalize team abbreviations in boxscores
boxscores_df['away_team_abbrev_norm'] = boxscores_df['away_team_abbreviation'].apply(normalize_abbr)
boxscores_df['home_team_abbrev_norm'] = boxscores_df['home_team_abbreviation'].apply(normalize_abbr)

# Create lookup key for boxscores (using batting_r for runs/scores)
boxscores_df['match_key'] = (
    boxscores_df['away_team_abbrev_norm'] + '|' +
    boxscores_df['home_team_abbrev_norm'] + '|' +
    boxscores_df['away_batting_r'].astype(str) + '-' +
    boxscores_df['home_batting_r'].astype(str)
)

# Create lookup dictionary: match_key -> list of game_pks
game_pk_lookup = {}
for _, row in boxscores_df.iterrows():
    key = row['match_key']
    game_pk = row['game_pk']
    
    # Handle multiple games with same key (doubleheaders)
    if key not in game_pk_lookup:
        game_pk_lookup[key] = [game_pk]
    else:
        game_pk_lookup[key].append(game_pk)

print(f"Created lookup with {len(game_pk_lookup)} unique match keys")

# Track doubleheaders
doubleheaders = {k: v for k, v in game_pk_lookup.items() if len(v) > 1}
if doubleheaders:
    print(f"Found {len(doubleheaders)} doubleheader match keys")

print("\n" + "="*60)
print("STEP 2: Adding game_pk column to game outlook files")
print("="*60)

# Process each game outlook file
outlook_files = sorted(glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
total_games = 0
matched_games = 0
unmatched_games = 0
doubleheader_used = {}  # Track which game_pk we used for doubleheaders

for outlook_file in outlook_files:
    df = pd.read_csv(outlook_file)
    
    # Normalize team abbreviations
    df['away_abbr_norm'] = df['away_team_abbreviation'].apply(normalize_abbr)
    df['home_abbr_norm'] = df['home_team_abbreviation'].apply(normalize_abbr)
    
    # Create match key
    df['match_key'] = (
        df['away_abbr_norm'] + '|' +
        df['home_abbr_norm'] + '|' +
        df['away_team_score'].astype(str) + '-' +
        df['home_team_score'].astype(str)
    )
    
    # Add game_pk column
    game_pks = []
    for _, row in df.iterrows():
        key = row['match_key']
        if key in game_pk_lookup:
            available_pks = game_pk_lookup[key]
            
            if len(available_pks) == 1:
                # Single match
                game_pks.append(available_pks[0])
                matched_games += 1
            else:
                # Doubleheader - use the first available one that hasn't been used yet
                used_for_key = doubleheader_used.get(key, [])
                
                # Find first unused pk
                pk_to_use = None
                for pk in available_pks:
                    if pk not in used_for_key:
                        pk_to_use = pk
                        break
                
                if pk_to_use is None:
                    # All used, cycle back (shouldn't happen if data is consistent)
                    pk_to_use = available_pks[len(used_for_key) % len(available_pks)]
                
                game_pks.append(pk_to_use)
                
                # Mark as used
                if key not in doubleheader_used:
                    doubleheader_used[key] = []
                doubleheader_used[key].append(pk_to_use)
                
                matched_games += 1
        else:
            print(f"  WARNING: No match for {key} in {os.path.basename(outlook_file)}")
            game_pks.append(None)
            unmatched_games += 1
    
    df['game_pk'] = game_pks
    
    # Drop temporary columns
    df = df.drop(['away_abbr_norm', 'home_abbr_norm', 'match_key'], axis=1)
    
    # Reorder columns to put game_pk as column 1 (after id which is column 0)
    cols = df.columns.tolist()
    cols.remove('game_pk')
    cols.insert(1, 'game_pk')
    df = df[cols]
    
    # Save back
    df.to_csv(outlook_file, index=False)
    
    total_games += len(df)

print(f"\nTotal games processed: {total_games}")
print(f"Matched games: {matched_games}")
print(f"Unmatched games: {unmatched_games}")
print(f"Success rate: {matched_games/total_games*100:.2f}%")

print("\n" + "="*60)
print("STEP 3: Reordering games to match boxscore files")
print("="*60)

# Now reorder each outlook file to match the boxscore file order
boxscore_files = sorted(glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv'))

files_reordered = 0
games_reordered = 0

for boxscore_file in boxscore_files:
    # Extract date from filename
    date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
    outlook_file = f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date_str}.csv'
    
    if not os.path.exists(outlook_file):
        print(f"  WARNING: No outlook file for {date_str}")
        continue
    
    # Read both files
    boxscore_df = pd.read_csv(boxscore_file)
    outlook_df = pd.read_csv(outlook_file)
    
    # Get the order of game_pks from boxscore
    boxscore_order = boxscore_df['game_pk'].tolist()
    
    # Reorder outlook to match
    # Create a mapping of game_pk to row
    outlook_dict = {row['game_pk']: row for _, row in outlook_df.iterrows()}
    
    # Build reordered dataframe
    reordered_rows = []
    for game_pk in boxscore_order:
        if game_pk in outlook_dict:
            reordered_rows.append(outlook_dict[game_pk])
        else:
            print(f"  WARNING: game_pk {game_pk} in boxscore but not in outlook for {date_str}")
    
    if len(reordered_rows) > 0:
        reordered_df = pd.DataFrame(reordered_rows)
        reordered_df.to_csv(outlook_file, index=False)
        files_reordered += 1
        games_reordered += len(reordered_df)

print(f"\nFiles reordered: {files_reordered}")
print(f"Games reordered: {games_reordered}")

print("\n" + "="*60)
print("STEP 4: Verifying alignment")
print("="*60)

# Verify alignment by checking a few files
verification_files = boxscore_files[:5]
all_aligned = True

for boxscore_file in verification_files:
    date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
    outlook_file = f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date_str}.csv'
    
    if not os.path.exists(outlook_file):
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    outlook_df = pd.read_csv(outlook_file)
    
    boxscore_pks = boxscore_df['game_pk'].tolist()
    outlook_pks = outlook_df['game_pk'].tolist()
    
    if boxscore_pks == outlook_pks:
        print(f"  ✓ {date_str}: {len(boxscore_pks)} games aligned")
    else:
        print(f"  ✗ {date_str}: MISALIGNED")
        all_aligned = False

print("\n" + "="*60)
if all_aligned:
    print("✓ SUCCESS: All game outlook files aligned with boxscores!")
else:
    print("✗ WARNING: Some files may not be perfectly aligned")
print("="*60)
