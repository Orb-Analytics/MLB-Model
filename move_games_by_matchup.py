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

# Step 1: Load boxscore data to get the correct order
print("Step 1: Loading boxscore files to establish correct order...")
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
correct_order = []  # List of (date, position, game_pk, away, home)

for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    for position, row in df.iterrows():
        correct_order.append({
            'date': date,
            'position': position,
            'game_pk': int(row['game_pk']),
            'away_team': row['away_team_abbreviation'],
            'home_team': row['home_team_abbreviation']
        })

print(f"  Loaded {len(correct_order)} games from boxscores across {len(boxscore_files)} dates")

# Step 2: Load outlook files
print("\nStep 2: Loading outlook files...")
outlook_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv'))
outlook_data = {}
total_games = 0

for file in outlook_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    # Apply team abbreviation mapping
    df['away_team_abbreviation'] = df['away_team_abbreviation'].apply(apply_abbr_mapping)
    df['home_team_abbreviation'] = df['home_team_abbreviation'].apply(apply_abbr_mapping)
    outlook_data[date] = df
    total_games += len(df)

print(f"  Loaded {len(outlook_data)} files with {total_games} total games")

# Step 3: Build mapping from matchup to correct location
print("\nStep 3: Building matchup to correct location mapping...")
matchup_to_correct = {}  # (away, home) -> {date, position, game_pk}
for entry in correct_order:
    key = (entry['away_team'], entry['home_team'])
    if key in matchup_to_correct:
        print(f"  WARNING: Duplicate matchup {key}")
    matchup_to_correct[key] = entry

# Step 4: Analyze current outlook locations and determine moves needed
print("\nStep 4: Analyzing current locations...")
current_locations = []  # List of games with their current and correct locations
games_by_pk = {}  # game_pk -> {current_date, correct_date, current_pos, correct_pos}

for date, df in outlook_data.items():
    for idx, row in df.iterrows():
        away = row['away_team_abbreviation']
        home = row['home_team_abbreviation']
        matchup = (away, home)
        
        if matchup in matchup_to_correct:
            correct_info = matchup_to_correct[matchup]
            game_pk = correct_info['game_pk']
            
            current_loc = {
                'game_pk': game_pk,
                'away_team': away,
                'home_team': home,
                'current_date': date,
                'current_position': idx,
                'correct_date': correct_info['date'],
                'correct_position': correct_info['position'],
                'row_data': row.to_dict()
            }
            current_locations.append(current_loc)
            games_by_pk[game_pk] = current_loc

print(f"  Matched {len(current_locations)} games to boxscores")

# Step 5: Determine which games need to move
print("\nStep 5: Determining games that need to move...")
moves_needed = []
for loc in current_locations:
    if loc['current_date'] != loc['correct_date']:
        moves_needed.append(loc)
        print(f"  Game {loc['game_pk']}: {loc['away_team']}@{loc['home_team']}")
        print(f"    Currently: {loc['current_date']} pos {loc['current_position']}")
        print(f"    Should be: {loc['correct_date']} pos {loc['correct_position']}")

print(f"\nTotal games to move: {len(moves_needed)}")

if len(moves_needed) == 0:
    print("\n✅ All games are already in the correct date files!")
    exit(0)

# Step 6: Group moves by target date and sort by position (descending)
print("\nStep 6: Grouping moves by target date...")
moves_by_target = defaultdict(list)
for move in moves_needed:
    moves_by_target[move['correct_date']].append(move)

# Sort each target's moves by position in descending order
for target_date in sorted(moves_by_target.keys()):
    moves_by_target[target_date].sort(key=lambda x: x['correct_position'], reverse=True)
    print(f"  {target_date}: {len(moves_by_target[target_date])} games at positions {[m['correct_position'] for m in moves_by_target[target_date]]}")

# Step 7: Extract games from source dates
print("\nStep 7: Extracting games from source dates...")
for move in moves_needed:
    game_pk = move['game_pk']
    from_date = move['current_date']
    matchup = (move['away_team'], move['home_team'])
    
    df = outlook_data[from_date]
    # Find the game by matchup
    mask = (df['away_team_abbreviation'] == matchup[0]) & (df['home_team_abbreviation'] == matchup[1])
    if mask.sum() > 0:
        # Remove from source
        outlook_data[from_date] = df[~mask].reset_index(drop=True)
        print(f"  Removed {move['away_team']}@{move['home_team']} from {from_date}")

# Step 8: Insert games into target dates in descending position order
print("\nStep 8: Inserting games into target dates...")
for target_date in sorted(moves_by_target.keys()):
    for move in moves_by_target[target_date]:  # Already sorted descending
        position = move['correct_position']
        game_row = move['row_data']
        
        # Update game_pk in the row data
        game_row['game_pk'] = move['game_pk']
        
        # Create target dataframe если if it doesn't exist
        if target_date not in outlook_data or len(outlook_data[target_date]) == 0:
            outlook_data[target_date] = pd.DataFrame(columns=list(game_row.keys()))
        
        df = outlook_data[target_date]
        
        # Insert at position
        if position >= len(df):
            # Append at end
            new_df = pd.concat([df, pd.DataFrame([game_row])], ignore_index=True)
        else:
            # Insert at position
            top = df.iloc[:position]
            bottom = df.iloc[position:]
            new_df = pd.concat([top, pd.DataFrame([game_row]), bottom], ignore_index=True)
        
        outlook_data[target_date] = new_df
        print(f"  Inserted {move['away_team']}@{move['home_team']} (game {move['game_pk']}) at position {position} in {target_date}")

# Step 9: Save all files
print("\nStep 9: Saving files...")
for date, df in outlook_data.items():
    if len(df) > 0:
        file_path = f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv'
        df.to_csv(file_path, index=False)

# Step 10: Final verification
print("\n" + "="*80)
print("Step 10: Verification...")
final_total = sum(len(df) for df in outlook_data.values())
print(f"Games before: {total_games}")
print(f"Games after: {final_total}")

if final_total != total_games:
    print(f"⚠️  WARNING: Lost {total_games - final_total} games!")
else:
    print("✅ No games lost!")

# Check alignment
perfect_dates = 0
position_matches = 0
total_checked = 0

for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    if date in outlook_data:
        boxscore_df = pd.read_csv(file)
        outlook_df = outlook_data[date]
        
        if len(boxscore_df) == len(outlook_df):
            date_perfect = True
            for i in range(len(boxscore_df)):
                box_pk = int(boxscore_df.iloc[i]['game_pk'])
                
                # Check matchup match
                out_away = outlook_df.iloc[i]['away_team_abbreviation']
                out_home = outlook_df.iloc[i]['home_team_abbreviation']
                box_away = boxscore_df.iloc[i]['away_team_abbreviation']
                box_home = boxscore_df.iloc[i]['home_team_abbreviation']
                
                total_checked += 1
                if out_away == box_away and out_home == box_home:
                    position_matches += 1
                else:
                    date_perfect = False
            
            if date_perfect:
                perfect_dates += 1

print(f"\nPerfect dates: {perfect_dates}/{len(boxscore_files)} ({100*perfect_dates/len(boxscore_files):.1f}%)")
print(f"Position matches: {position_matches}/{total_checked} ({100*position_matches/total_checked:.1f}%)")
print("="*80)
