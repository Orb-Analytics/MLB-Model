import pandas as pd
import glob
import os

print("="*70)
print("Identifying missing 2012 games after date alignment")
print("="*70)

# Read all MLB boxscores
boxscore_files = sorted(glob.glob('data/2012_data/mlb_data/raw/boxscores/*.csv'))

# Read all BDL outlook
outlook_files = sorted(glob.glob('data/2012_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))

# Collect all game_pks
all_boxscore_pks = set()
all_outlook_pks = set()

for file in boxscore_files:
    df = pd.read_csv(file)
    all_boxscore_pks.update(df['game_pk'].tolist())

for file in outlook_files:
    df = pd.read_csv(file)
    if 'game_pk' in df.columns:
        # Filter out None/NaN values
        pks = df['game_pk'].dropna().tolist()
        all_outlook_pks.update([int(pk) for pk in pks])

print(f"Total unique game_pks in boxscores: {len(all_boxscore_pks)}")
print(f"Total unique game_pks in outlook: {len(all_outlook_pks)}")

# Find missing game_pks
missing_pks = all_boxscore_pks - all_outlook_pks

print(f"\n{'='*70}")
print(f"Found {len(missing_pks)} game_pks in boxscores but NOT in outlook:")
print("="*70)

if len(missing_pks) > 0:
    # Get details for each missing game
    all_boxscores = []
    for file in boxscore_files:
        df = pd.read_csv(file)
        date_str = os.path.basename(file).replace('boxscores_', '').replace('.csv', '')
        df['file_date'] = date_str
        all_boxscores.append(df)
    
    boxscores_df = pd.concat(all_boxscores, ignore_index=True)
    
    for game_pk in sorted(missing_pks):
        game = boxscores_df[boxscores_df['game_pk'] == game_pk].iloc[0]
        print(f"\ngame_pk: {game_pk}")
        print(f"  Date: {game['file_date']}")
        print(f"  Matchup: {game['away_team_abbreviation']} @ {game['home_team_abbreviation']}")
        print(f"  Score: {int(game['away_batting_r'])}-{int(game['home_batting_r'])}")

# Also check for games in outlook but not in boxscores (shouldn't happen)
extra_pks = all_outlook_pks - all_boxscore_pks
if len(extra_pks) > 0:
    print(f"\n{'='*70}")
    print(f"WARNING: {len(extra_pks)} game_pks in outlook but NOT in boxscores:")
    print("="*70)
    for pk in sorted(extra_pks):
        print(f"  {pk}")

print(f"\n{'='*70}")
print(f"SUMMARY:")
print(f"  Games in MLB boxscores: {len(all_boxscore_pks)}")
print(f"  Games in BDL outlook: {len(all_outlook_pks)}")
print(f"  Missing from outlook: {len(missing_pks)}")
print("="*70)
