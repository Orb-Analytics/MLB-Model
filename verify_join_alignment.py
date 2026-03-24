import pandas as pd
import glob

print("="*80)
print("VERIFYING: ALL THREE DATASETS CAN BE JOINED PERFECTLY")
print("="*80)

# Load all three datasets for a sample date
test_date = '2009-04-06'

print(f"\nTesting with date: {test_date}")
print("-"*80)

# Load the three files
boxscore_df = pd.read_csv(f'data/2009_data/mlb_data/raw/boxscores/boxscores_{test_date}.csv')
pitcher_df = pd.read_csv(f'data/2009_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{test_date}.csv')
outlook_df = pd.read_csv(f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{test_date}.csv')

print(f"\nRow counts:")
print(f"  Boxscore: {len(boxscore_df)} games")
print(f"  Starting Pitcher: {len(pitcher_df)} games")
print(f"  Game Outlook: {len(outlook_df)} games")

if len(boxscore_df) == len(pitcher_df) == len(outlook_df):
    print(f"  ✅ All have same row count")
else:
    print(f"  ❌ Row counts don't match!")

# Check row-by-row alignment
print(f"\nRow-by-row verification:")
all_match = True
for i in range(len(boxscore_df)):
    box_pk = int(boxscore_df.iloc[i]['game_pk'])
    pitch_pk = int(pitcher_df.iloc[i]['game_pk'])
    out_pk = int(outlook_df.iloc[i]['game_pk'])
    
    box_away = boxscore_df.iloc[i]['away_team_abbreviation']
    box_home = boxscore_df.iloc[i]['home_team_abbreviation']
    pitch_away = pitcher_df.iloc[i]['away_starter_team']
    pitch_home = pitcher_df.iloc[i]['home_starter_team']
    out_away = outlook_df.iloc[i]['away_team_abbreviation']
    out_home = outlook_df.iloc[i]['home_team_abbreviation']
    
    if box_pk != pitch_pk or box_pk != out_pk:
        print(f"  Row {i}: game_pk mismatch - box={box_pk}, pitch={pitch_pk}, out={out_pk}")
        all_match = False
    
    if box_away != pitch_away or box_away != out_away or box_home != pitch_home or box_home != out_home:
        print(f"  Row {i}: teams mismatch")
        print(f"    Box: {box_away}@{box_home}")
        print(f"    Pitch: {pitch_away}@{pitch_home}")
        print(f"    Out: {out_away}@{out_home}")
        all_match = False

if all_match:
    print(f"  ✅ All {len(boxscore_df)} rows match perfectly!")

# Now test across ALL dates
print("\n" + "="*80)
print("TESTING ALL 181 DATES")
print("="*80)

boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
total_games = 0
perfect_dates = 0
mismatches = []

for box_file in boxscore_files:
    date = box_file.split('_')[-1].replace('.csv', '')
    
    try:
        box_df = pd.read_csv(box_file)
        pitch_df = pd.read_csv(f'data/2009_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date}.csv')
        out_df = pd.read_csv(f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv')
    except FileNotFoundError as e:
        mismatches.append(f"{date}: File not found - {e}")
        continue
    
    # Check counts
    if len(box_df) != len(pitch_df) or len(box_df) != len(out_df):
        mismatches.append(f"{date}: Count mismatch - box={len(box_df)}, pitch={len(pitch_df)}, out={len(out_df)}")
        continue
    
    # Check each row
    date_perfect = True
    for i in range(len(box_df)):
        total_games += 1
        
        box_pk = int(box_df.iloc[i]['game_pk'])
        pitch_pk = int(pitch_df.iloc[i]['game_pk'])
        out_pk = int(out_df.iloc[i]['game_pk'])
        
        if box_pk != pitch_pk or box_pk != out_pk:
            mismatches.append(f"{date} row {i}: game_pk mismatch")
            date_perfect = False
            break
        
        box_away = box_df.iloc[i]['away_team_abbreviation']
        box_home = box_df.iloc[i]['home_team_abbreviation']
        pitch_away = pitch_df.iloc[i]['away_starter_team']
        pitch_home = pitch_df.iloc[i]['home_starter_team']
        out_away = out_df.iloc[i]['away_team_abbreviation']
        out_home = out_df.iloc[i]['home_team_abbreviation']
        
        if box_away != pitch_away or box_away != out_away or box_home != pitch_home or box_home != out_home:
            mismatches.append(f"{date} row {i}: team mismatch")
            date_perfect = False
            break
    
    if date_perfect:
        perfect_dates += 1

print(f"\nResults:")
print(f"  Total dates: {len(boxscore_files)}")
print(f"  Perfect dates: {perfect_dates}")
print(f"  Total games checked: {total_games}")

if mismatches:
    print(f"\n❌ Found {len(mismatches)} mismatches:")
    for m in mismatches[:10]:
        print(f"  - {m}")
    if len(mismatches) > 10:
        print(f"  ... and {len(mismatches)-10} more")
else:
    print(f"\n✅ PERFECT ALIGNMENT ACROSS ALL THREE DATASETS!")
    print(f"   All {total_games} games can be joined perfectly")
    print(f"   Row-by-row match on:")
    print(f"     • game_pk")
    print(f"     • away_team")
    print(f"     • home_team")
    print(f"     • date")
    print(f"     • position in file")

print("="*80)
