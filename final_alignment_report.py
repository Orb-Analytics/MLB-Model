import pandas as pd
import glob

print("="*80)
print("FINAL 2009 OUTLOOK-BOXSCORE ALIGNMENT REPORT")
print("="*80)

# Count games
outlook_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_*.csv'))
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))

outlook_games = sum(len(pd.read_csv(f)) for f in outlook_files)
boxscore_games = sum(len(pd.read_csv(f)) for f in boxscore_files)

print(f"\nFiles:")
print(f"  Outlook files: {len(outlook_files)}")
print(f"  Boxscore files: {len(boxscore_files)}")

print(f"\nGames:")
print(f"  Outlook games: {outlook_games}")
print(f"  Boxscore games: {boxscore_games}")

# Check alignment
ABBR_MAPPING = {'ARI': 'AZ', 'CHW': 'CWS', 'MIA': 'FLA'}

perfect_count = 0
total_positions = 0
matched_positions = 0
mismatches = []

for box_file in boxscore_files:
    date = box_file.split('_')[-1].replace('.csv', '')
    out_file = f'data/2009_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv'
    
    try:
        box_df = pd.read_csv(box_file)
        out_df = pd.read_csv(out_file)
    except FileNotFoundError:
        mismatches.append(f"{date}: Outlook file missing")
        continue
    
    if len(box_df) != len(out_df):
        mismatches.append(f"{date}: Count mismatch (box={len(box_df)}, out={len(out_df)})")
        continue
    
    date_perfect = True
    for i in range(len(box_df)):
        total_positions += 1
        
        box_pk = int(box_df.iloc[i]['game_pk'])
        out_pk = out_df.iloc[i]['game_pk']
        
        box_away = box_df.iloc[i]['away_team_abbreviation']
        box_home = box_df.iloc[i]['home_team_abbreviation']
        out_away = out_df.iloc[i]['away_team_abbreviation']
        out_home = out_df.iloc[i]['home_team_abbreviation']
        
        # Apply mapping to outlook for comparison
        out_away_mapped = ABBR_MAPPING.get(out_away, out_away)
        out_home_mapped = ABBR_MAPPING.get(out_home, out_home)
        
        if pd.isna(out_pk):
            mismatches.append(f"{date} pos {i}: Missing game_pk")
            date_perfect = False
        elif int(out_pk) != box_pk:
            mismatches.append(f"{date} pos {i}: game_pk mismatch (box={box_pk}, out={out_pk})")  
            date_perfect = False
        elif out_away_mapped != box_away or out_home_mapped != box_home:
            mismatches.append(f"{date} pos {i}: Team mismatch ({out_away_mapped}@{out_home_mapped} vs {box_away}@{box_home})")
            date_perfect = False
        else:
            matched_positions += 1
    
    if date_perfect:
        perfect_count += 1

print(f"\nAlignment:")
print(f"  Perfect dates: {perfect_count}/{len(boxscore_files)} ({100*perfect_count/len(boxscore_files):.1f}%)")
print(f"  Matched positions: {matched_positions}/{total_positions} ({100*matched_positions/total_positions:.1f}%)")

if mismatches:
    print(f"\n⚠️  Found {len(mismatches)} mismatches:")
    for m in mismatches[:20]:
        print(f"  - {m}")
    if len(mismatches) > 20:
        print(f"  ... and {len(mismatches)-20} more")
else:
    print(f"\n✅ PERFECT ALIGNMENT!")
    print(f"   All {total_positions} games match exactly")
    print(f"   Order: ✓  Dates: ✓  Teams: ✓  Game PKs: ✓")

print("="*80)
