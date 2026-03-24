import pandas as pd
import glob
from collections import defaultdict

# Step 1: Load all outlook files
outlook_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv'))
print(f"Step 1: Loading {len(outlook_files)} outlook files...")
outlook_data = {}
total_games = 0
for file in outlook_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    outlook_data[date] = df
    total_games += len(df)
print(f"  Loaded {len(outlook_data)} files with {total_games} total games")

# Step 2: Build game_pk to current date mapping
print("Step 2: Building game_pk to date mapping...")
game_pk_to_date = {}
for date, df in outlook_data.items():
    for idx, row in df.iterrows():
        if pd.notna(row.get('game_pk')):
            game_pk_to_date[int(row['game_pk'])] = date
print(f"  Found {len(game_pk_to_date)} games with game_pk")

# Step 3: Load boxscore data to determine correct date and position
print("Step 3: Determining which games need to move...")
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
boxscore_order = {}
for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    for position, game_pk in enumerate(df['game_pk']):
        boxscore_order[int(game_pk)] = {
            'correct_date': date,
            'correct_position': position
        }

# Find games that need to move
moves_needed = []
for game_pk, correct_info in boxscore_order.items():
    if game_pk in game_pk_to_date:
        current_date = game_pk_to_date[game_pk]
        correct_date = correct_info['correct_date']
        if current_date != correct_date:
            moves_needed.append({
                'game_pk': game_pk,
                'from_date': current_date,
                'to_date': correct_date,
                'to_position': correct_info['correct_position']
            })
            print(f"  Game {game_pk}: {current_date} → {correct_date} (position {correct_info['correct_position']})")

print(f"\nTotal games to move: {len(moves_needed)}")

# Step 4: Group moves by target date and sort by position (descending)
print("Step 4: Moving games...")
moves_by_target = defaultdict(list)
for move in moves_needed:
    moves_by_target[move['to_date']].append(move)

# Sort each target's moves by position in descending order
for target_date in moves_by_target:
    moves_by_target[target_date].sort(key=lambda x: x['to_position'], reverse=True)
    print(f"  {target_date}: {len(moves_by_target[target_date])} games")
    for move in moves_by_target[target_date]:
        print(f"    - Game {move['game_pk']} at position {move['to_position']}")

# Extract games from source dates
games_to_move = {}
for move in moves_needed:
    game_pk = move['game_pk']
    from_date = move['from_date']
    
    # Find and extract the game
    df = outlook_data[from_date]
    game_row = df[df['game_pk'] == game_pk]
    if len(game_row) > 0:
        games_to_move[game_pk] = game_row.iloc[0].to_dict()
        # Remove from source
        outlook_data[from_date] = df[df['game_pk'] != game_pk].reset_index(drop=True)

print(f"  Extracted {len(games_to_move)} games from source dates")

# Insert games into target dates in descending position order
for target_date, moves in moves_by_target.items():
    for move in moves:  # Already sorted descending
        game_pk = move['game_pk']
        position = move['to_position']
        
        if game_pk in games_to_move:
            game_row = games_to_move[game_pk]
            
            # Create target dataframe if it doesn't exist
            if target_date not in outlook_data:
                outlook_data[target_date] = pd.DataFrame(columns=list(game_row.keys()))
            
            df = outlook_data[target_date]
            
            # Insert at position using pd.concat
            if position >= len(df):
                # Append at end
                new_df = pd.concat([df, pd.DataFrame([game_row])], ignore_index=True)
            else:
                # Insert at position
                top = df.iloc[:position]
                bottom = df.iloc[position:]
                new_df = pd.concat([top, pd.DataFrame([game_row]), bottom], ignore_index=True)
            
            outlook_data[target_date] = new_df
            print(f"    Inserted game {game_pk} at position {position} in {target_date}")

# Step 5: Sort each date by boxscore order
print("\nStep 5: Final sort by boxscore order...")
for date, df in outlook_data.items():
    if len(df) > 0:
        # Create box_order column for sorting
        df['box_order'] = df['game_pk'].map(
            lambda pk: boxscore_order[int(pk)]['correct_position'] if pd.notna(pk) and int(pk) in boxscore_order else 9999
        )
        df = df.sort_values('box_order').drop('box_order', axis=1).reset_index(drop=True)
        outlook_data[date] = df

# Step 6: Save all files
print("Step 6: Saving files...")
for date, df in outlook_data.items():
    file_path = f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv'
    df.to_csv(file_path, index=False)

# Final verification
print("\n" + "="*60)
print("Step 7: Verification...")
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
                out_pk = outlook_df.iloc[i]['game_pk']
                if pd.notna(out_pk):
                    out_pk = int(out_pk)
                    total_checked += 1
                    if box_pk == out_pk:
                        position_matches += 1
                    else:
                        date_perfect = False
            if date_perfect:
                perfect_dates += 1

print(f"\nPerfect dates: {perfect_dates}/{len(boxscore_files)} ({100*perfect_dates/len(boxscore_files):.1f}%)")
print(f"Position matches: {position_matches}/{total_checked} ({100*position_matches/total_checked:.1f}%)")
print("="*60)
