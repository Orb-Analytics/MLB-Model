import pandas as pd
import glob
import os

print("="*70)
print("ROW-BY-ROW ALIGNMENT VERIFICATION")
print("Verifying that boxscores, pitchers, and outlook align perfectly")
print("="*70)

boxscore_files = sorted(glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv'))

perfect_alignment = True
total_rows = 0
total_files = 0

# Check a few sample files in detail
sample_dates = ['2011-04-01', '2011-05-15', '2011-07-04', '2011-08-20', '2011-09-28']

print("\n" + "="*70)
print("DETAILED SAMPLE CHECK")
print("="*70)

for date in sample_dates:
    boxscore_file = f'data/2011_data/mlb_data/raw/boxscores/boxscores_{date}.csv'
    pitcher_file = f'data/2011_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date}.csv'
    outlook_file = f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv'
    
    if not all([os.path.exists(f) for f in [boxscore_file, pitcher_file, outlook_file]]):
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    pitcher_df = pd.read_csv(pitcher_file)
    outlook_df = pd.read_csv(outlook_file)
    
    print(f"\n{date} ({len(boxscore_df)} games):")
    print("-" * 70)
    
    # Show first few rows side by side
    for i in range(min(3, len(boxscore_df))):
        b_pk = boxscore_df.iloc[i]['game_pk']
        p_pk = pitcher_df.iloc[i]['game_pk']
        o_pk = outlook_df.iloc[i]['game_pk']
        
        b_away = boxscore_df.iloc[i]['away_team_abbreviation']
        b_home = boxscore_df.iloc[i]['home_team_abbreviation']
        b_score = f"{boxscore_df.iloc[i]['away_batting_r']}-{boxscore_df.iloc[i]['home_batting_r']}"
        
        o_away = outlook_df.iloc[i]['away_team_abbreviation']
        o_home = outlook_df.iloc[i]['home_team_abbreviation']
        o_score = f"{outlook_df.iloc[i]['away_team_score']}-{outlook_df.iloc[i]['home_team_score']}"
        
        match = "✓" if b_pk == p_pk == o_pk else "✗"
        
        print(f"  Row {i}: game_pk={b_pk}")
        print(f"    Boxscore: {b_away} @ {b_home} = {b_score}")
        print(f"    Pitcher:  game_pk={p_pk}")
        print(f"    Outlook:  game_pk={o_pk}, {o_away} @ {o_home} = {o_score}")
        print(f"    Alignment: {match}")

print("\n" + "="*70)
print("COMPREHENSIVE FILE-BY-FILE CHECK")
print("="*70)

misaligned_rows = []

for boxscore_file in boxscore_files:
    date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
    pitcher_file = f'data/2011_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date_str}.csv'
    outlook_file = f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date_str}.csv'
    
    if not all([os.path.exists(f) for f in [pitcher_file, outlook_file]]):
        continue
    
    boxscore_df = pd.read_csv(boxscore_file)
    pitcher_df = pd.read_csv(pitcher_file)
    outlook_df = pd.read_csv(outlook_file)
    
    total_files += 1
    
    # Check row counts match
    if not (len(boxscore_df) == len(pitcher_df) == len(outlook_df)):
        print(f"✗ {date_str}: Row count mismatch")
        perfect_alignment = False
        continue
    
    # Check each row's game_pk
    for i in range(len(boxscore_df)):
        b_pk = boxscore_df.iloc[i]['game_pk']
        p_pk = pitcher_df.iloc[i]['game_pk']
        o_pk = outlook_df.iloc[i]['game_pk']
        
        total_rows += 1
        
        if not (b_pk == p_pk == o_pk):
            print(f"✗ {date_str} row {i}: game_pks don't match - B:{b_pk} P:{p_pk} O:{o_pk}")
            misaligned_rows.append((date_str, i, b_pk, p_pk, o_pk))
            perfect_alignment = False

print(f"\n{'='*70}")
print("FINAL RESULTS")
print("="*70)
print(f"Total files checked: {total_files}")
print(f"Total rows checked: {total_rows}")
print(f"Misaligned rows: {len(misaligned_rows)}")

if perfect_alignment:
    print(f"\n{'🎉 ' * 10}")
    print("PERFECT ALIGNMENT CONFIRMED!")
    print(f"All {total_rows} rows across {total_files} files align perfectly.")
    print("The game_pk columns match row-by-row across all three datasets.")
    print("You can safely merge/join these datasets on row index.")
    print(f"{'🎉 ' * 10}")
else:
    print(f"\n⚠️  Found {len(misaligned_rows)} misaligned rows")
    print("First few misalignments:")
    for date, row, b, p, o in misaligned_rows[:5]:
        print(f"  {date} row {row}: B={b} P={p} O={o}")

print("="*70)

# Additional verification: Check that all game_pks are unique across entire dataset
print("\n" + "="*70)
print("UNIQUENESS CHECK")
print("="*70)

all_boxscore_pks = []
all_outlook_pks = []

for boxscore_file in boxscore_files:
    date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
    outlook_file = f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date_str}.csv'
    
    if os.path.exists(outlook_file):
        boxscore_df = pd.read_csv(boxscore_file)
        outlook_df = pd.read_csv(outlook_file)
        
        all_boxscore_pks.extend(boxscore_df['game_pk'].tolist())
        all_outlook_pks.extend(outlook_df['game_pk'].tolist())

print(f"Total game_pks in boxscores: {len(all_boxscore_pks)}")
print(f"Unique game_pks in boxscores: {len(set(all_boxscore_pks))}")
print(f"Total game_pks in outlook: {len(all_outlook_pks)}")
print(f"Unique game_pks in outlook: {len(set(all_outlook_pks))}")

if len(all_boxscore_pks) == len(set(all_boxscore_pks)):
    print("✓ All boxscore game_pks are unique")
else:
    print("✗ Duplicate game_pks found in boxscores")

if len(all_outlook_pks) == len(set(all_outlook_pks)):
    print("✓ All outlook game_pks are unique")
else:
    print("✗ Duplicate game_pks found in outlook")

# Check if sets are identical
boxscore_set = set(all_boxscore_pks)
outlook_set = set(all_outlook_pks)

if boxscore_set == outlook_set:
    print("✓ Boxscore and outlook contain exactly the same game_pks")
else:
    missing_in_outlook = boxscore_set - outlook_set
    missing_in_boxscore = outlook_set - boxscore_set
    
    if missing_in_outlook:
        print(f"✗ {len(missing_in_outlook)} game_pks in boxscore but not in outlook:")
        print(f"  {list(missing_in_outlook)[:5]}...")
    
    if missing_in_boxscore:
        print(f"✗ {len(missing_in_boxscore)} game_pks in outlook but not in boxscore:")
        print(f"  {list(missing_in_boxscore)[:5]}...")

print("="*70)
