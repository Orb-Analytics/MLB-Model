import pandas as pd
import glob
from collections import defaultdict

# Team abbreviation mapping
ABBR_MAPPING = {
    'ARI': 'AZ',
    'CHW': 'CWS',
    'MIA': 'FLA'
}

def apply_abbr_mapping(team_abbr):
    """Apply historical team abbreviation mapping"""
    if pd.isna(team_abbr):
        return team_abbr
    return ABBR_MAPPING.get(str(team_abbr).strip(), str(team_abbr).strip())

print("="*80)
print("REBUILDING 2009 OUTLOOK FILES TO MATCH BOXSCORE ORDER")
print("="*80)

# Step 1: Load all boxscores to get the correct structure
print("\nStep 1: Loading boxscores to determine correct structure...")
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
correct_structure = defaultdict(list)  # date -> list of (position, game_pk, away, home)

for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    for position, row in df.iterrows():
        correct_structure[date].append({
            'position': position,
            'game_pk': int(row['game_pk']),
            'away_team': row['away_team_abbreviation'],
            'home_team': row['home_team_abbreviation']
        })

total_boxscore_games = sum(len(v) for v in correct_structure.values())
print(f"  {len(boxscore_files)} dates with {total_boxscore_games} total games")

# Step 2: Load all outlook files and build matchup index
print("\nStep 2: Loading all outlook files and indexing by matchup...")
all_outlook_games = {}  # (away, home) -> game_row
outlook_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv'))

for file in outlook_files:
    df = pd.read_csv(file)
    # Apply team abbreviation mapping
    df['away_team_abbreviation'] = df['away_team_abbreviation'].apply(apply_abbr_mapping)
    df['home_team_abbreviation'] = df['home_team_abbreviation'].apply(apply_abbr_mapping)
    
    for _, row in df.iterrows():
        away = row['away_team_abbreviation']
        home = row['home_team_abbreviation']
        matchup = (away, home)
        
        if matchup in all_outlook_games:
            print(f"  WARNING: Duplicate matchup {matchup}")
        else:
            all_outlook_games[matchup] = row.to_dict()

print(f"  Indexed {len(all_outlook_games)} unique outlook games")

# Step 3: Rebuild each date file according to boxscore structure
print("\nStep 3: Rebuilding date files to match boxscore structure...")
new_outlook_data = {}
matched_games = 0
missing_games = []

for date, games_list in sorted(correct_structure.items()):
    date_games = []
    
    for game_info in games_list:
        matchup = (game_info['away_team'], game_info['home_team'])
        
        if matchup in all_outlook_games:
            # Get the outlook game data
            game_row = all_outlook_games[matchup].copy()
            # Ensure game_pk is set correctly
            game_row['game_pk'] = game_info['game_pk']
            date_games.append(game_row)
            matched_games += 1
        else:
            missing_games.append(f"{date}: {matchup[0]}@{matchup[1]} (game_pk {game_info['game_pk']})")
    
    if date_games:
        new_outlook_data[date] = pd.DataFrame(date_games)
        print(f"  {date}: {len(date_games)} games")

print(f"\nMatched: {matched_games}/{total_boxscore_games} games")
if missing_games:
    print(f"\nMissing {len(missing_games)} games:")
    for msg in missing_games[:10]:
        print(f"  - {msg}")
    if len(missing_games) > 10:
        print(f"  ... and {len(missing_games) - 10} more")

# Step 4: Save all files
print("\nStep 4: Saving new outlook files...")
saved_count = 0
for date, df in new_outlook_data.items():
    file_path = f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv'
    df.to_csv(file_path, index=False)
    saved_count += 1

print(f"  Saved {saved_count} files")

# Step 5: Verification
print("\n" + "="*80)
print("VERIFICATION")
print("="*80)

perfect_dates = 0
position_matches = 0
total_checked = 0
mismatched_dates = []

for date, correct_games in sorted(correct_structure.items()):
    if date in new_outlook_data:
        outlook_df = new_outlook_data[date]
        
        if len(correct_games) != len(outlook_df):
            mismatched_dates.append(f"{date}: boxscore={len(correct_games)}, outlook={len(outlook_df)}")
            continue
        
        date_perfect = True
        for i, game_info in enumerate(correct_games):
            total_checked += 1
            out_away = outlook_df.iloc[i]['away_team_abbreviation']
            out_home = outlook_df.iloc[i]['home_team_abbreviation']
            
            if out_away == game_info['away_team'] and out_home == game_info['home_team']:
                position_matches += 1
            else:
                date_perfect = False
        
        if date_perfect:
            perfect_dates += 1
    else:
        mismatched_dates.append(f"{date}: no outlook file")

print(f"\nPerfect dates: {perfect_dates}/{len(correct_structure)} ({100*perfect_dates/len(correct_structure):.1f}%)")
print(f"Position matches: {position_matches}/{total_checked} ({100*position_matches/total_checked:.1f}%)")

if mismatched_dates:
    print(f"\n{len(mismatched_dates)} dates with mismatches:")
    for msg in mismatched_dates[:10]:
        print(f"  - {msg}")
    if len(mismatched_dates) > 10:
        print(f"  ... and {len(mismatched_dates) - 10} more")

print("="*80)
if perfect_dates == len(correct_structure) and position_matches == total_checked:
    print("✅ SUCCESS: All games perfectly aligned!")
else:
    print(f"⚠️  PARTIAL: {100*position_matches/total_checked:.1f}% aligned")
print("="*80)
