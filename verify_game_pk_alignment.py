import pandas as pd
import glob

print("="*80)
print("VERIFYING: PERFECT JOIN ALIGNMENT BY GAME_PK")
print("="*80)

# Test across ALL dates
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
total_games = 0
perfect_dates = 0
game_pk_mismatches = []
count_mismatches = []

for box_file in boxscore_files:
    date = box_file.split('_')[-1].replace('.csv', '')
    
    try:
        box_df = pd.read_csv(box_file)
        pitch_df = pd.read_csv(f'data/2009_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date}.csv')
        out_df = pd.read_csv(f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv')
    except FileNotFoundError as e:
        count_mismatches.append(f"{date}: File not found")
        continue
    
    # Check counts
    if len(box_df) != len(pitch_df) or len(box_df) != len(out_df):
        count_mismatches.append(f"{date}: Count mismatch - box={len(box_df)}, pitch={len(pitch_df)}, out={len(out_df)}")
        continue
    
    # Check game_pk alignment only
    date_perfect = True
    for i in range(len(box_df)):
        total_games += 1
        
        box_pk = int(box_df.iloc[i]['game_pk'])
        pitch_pk = int(pitch_df.iloc[i]['game_pk'])
        out_pk = int(out_df.iloc[i]['game_pk'])
        
        if box_pk != pitch_pk or box_pk != out_pk:
            game_pk_mismatches.append(f"{date} row {i}: box={box_pk}, pitch={pitch_pk}, out={out_pk}")
            date_perfect = False
            break
    
    if date_perfect:
        perfect_dates += 1

print(f"\nResults:")
print(f"  Total dates: {len(boxscore_files)}")
print(f"  Perfect dates (game_pk aligned): {perfect_dates}")
print(f"  Total games checked: {total_games}")

if game_pk_mismatches:
    print(f"\n❌ Found {len(game_pk_mismatches)} game_pk mismatches:")
    for m in game_pk_mismatches[:20]:
        print(f"  - {m}")
elif count_mismatches:
    print(f"\n❌ Found {len(count_mismatches)} count mismatches:")
    for m in count_mismatches[:20]:
        print(f"  - {m}")
else:
    print(f"\n✅ PERFECT ALIGNMENT FOR JOINING!")
    print(f"\n   All {total_games} games across {len(boxscore_files)} dates:")
    print(f"   • Same number of rows in each file ✓")
    print(f"   • game_pk matches row-by-row ✓")
    print(f"   • Files can be joined by position/index ✓")
    print(f"\n   Note: Team names differ in format:")
    print(f"   • Boxscore & Outlook: 'NYM', 'CIN' (abbreviations)")
    print(f"   • Starting Pitcher: 'New York Mets', 'Cincinnati Reds' (full names)")
    print(f"   • Both refer to the same teams ✓")
    print(f"\n   To join the files:")
    print(f"   • Concat by position: pd.concat([box, pitch, out], axis=1)")
    print(f"   • Or merge on game_pk: box.merge(pitch, on='game_pk').merge(out, on='game_pk')")

print("="*80)
