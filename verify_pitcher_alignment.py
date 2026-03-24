import pandas as pd
import glob

print("="*80)
print("VERIFYING GAME OUTLOOK vs STARTING PITCHER BOXSCORE ALIGNMENT")
print("="*80)

outlook_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv'))
pitcher_files = sorted(glob.glob('data/2009_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_*.csv'))

print(f"\nFiles:")
print(f"  Outlook files: {len(outlook_files)}")
print(f"  Pitcher files: {len(pitcher_files)}")

# Check alignment
perfect_count = 0
total_games = 0
matched_games = 0
mismatches = []

for pitcher_file in pitcher_files:
    date = pitcher_file.split('_')[-1].replace('.csv', '')
    outlook_file = f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv'
    
    try:
        pitcher_df = pd.read_csv(pitcher_file)
        outlook_df = pd.read_csv(outlook_file)
    except FileNotFoundError:
        mismatches.append(f"{date}: Outlook file missing")
        continue
    
    if len(pitcher_df) != len(outlook_df):
        mismatches.append(f"{date}: Count mismatch (pitcher={len(pitcher_df)}, outlook={len(outlook_df)})")
        continue
    
    date_perfect = True
    for i in range(len(pitcher_df)):
        total_games += 1
        
        pitcher_pk = int(pitcher_df.iloc[i]['game_pk'])
        outlook_pk = outlook_df.iloc[i]['game_pk']
        
        if pd.isna(outlook_pk):
            mismatches.append(f"{date} pos {i}: Outlook missing game_pk")
            date_perfect = False
        elif int(outlook_pk) != pitcher_pk:
            mismatches.append(f"{date} pos {i}: game_pk mismatch (pitcher={pitcher_pk}, outlook={int(outlook_pk)})")
            date_perfect = False
        else:
            matched_games += 1
    
    if date_perfect:
        perfect_count += 1

print(f"\nAlignment:")
print(f"  Perfect dates: {perfect_count}/{len(pitcher_files)} ({100*perfect_count/len(pitcher_files):.1f}%)")
print(f"  Matched positions: {matched_games}/{total_games} ({100*matched_games/total_games:.1f}%)")

if mismatches:
    print(f"\n⚠️  Found {len(mismatches)} mismatches:")
    for m in mismatches[:20]:
        print(f"  - {m}")
    if len(mismatches) > 20:
        print(f"  ... and {len(mismatches)-20} more")
else:
    print(f"\n✅ PERFECT ALIGNMENT!")
    print(f"   All {total_games} games match exactly between outlook and starting pitcher files")

print("="*80)
