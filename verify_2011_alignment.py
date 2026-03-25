import pandas as pd
import glob
import os

print("="*60)
print("Comprehensive 2011 Alignment Verification")
print("="*60)

boxscore_files = sorted(glob.glob('data/2011_data/mlb_data/raw/boxscores/*.csv'))
pitcher_files = sorted(glob.glob('data/2011_data/mlb_data/raw/starting_pitcher_boxscores/*.csv'))
outlook_files = sorted(glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))

print(f"\nFile counts:")
print(f"  Boxscores: {len(boxscore_files)}")
print(f"  Pitchers: {len(pitcher_files)}")
print(f"  Outlook: {len(outlook_files)}")

# Count total games
boxscore_count = sum(len(pd.read_csv(f)) for f in boxscore_files)
pitcher_count = sum(len(pd.read_csv(f)) for f in pitcher_files)
outlook_count = sum(len(pd.read_csv(f)) for f in outlook_files)

print(f"\nGame counts:")
print(f"  Boxscores: {boxscore_count}")
print(f"  Pitchers: {pitcher_count}")
print(f"  Outlook: {outlook_count}")
print(f"  All match 2430: {'✓' if boxscore_count == pitcher_count == outlook_count == 2430 else '✗'}")

# Verify alignment file by file
print(f"\n{'='*60}")
print("File-by-file alignment check:")
print(f"{'='*60}")

misaligned_files = []
aligned_files = 0

for boxscore_file in boxscore_files:
    date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
    pitcher_file = f'data/2011_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date_str}.csv'
    outlook_file = f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date_str}.csv'
    
    # Check if all files exist
    if not os.path.exists(pitcher_file):
        print(f"  ✗ {date_str}: Missing pitcher file")
        misaligned_files.append(date_str)
        continue
    
    if not os.path.exists(outlook_file):
        print(f"  ✗ {date_str}: Missing outlook file")
        misaligned_files.append(date_str)
        continue
    
    # Read files
    boxscore_df = pd.read_csv(boxscore_file)
    pitcher_df = pd.read_csv(pitcher_file)
    outlook_df = pd.read_csv(outlook_file)
    
    # Get game_pks
    boxscore_pks = boxscore_df['game_pk'].tolist()
    pitcher_pks = pitcher_df['game_pk'].tolist()
    outlook_pks = outlook_df['game_pk'].tolist()
    
    # Check alignment
    if boxscore_pks == pitcher_pks == outlook_pks:
        aligned_files += 1
    else:
        print(f"  ✗ {date_str}: MISALIGNED - B:{len(boxscore_pks)} P:{len(pitcher_pks)} O:{len(outlook_pks)}")
        misaligned_files.append(date_str)
        
        # Show discrepancies
        if boxscore_pks != pitcher_pks:
            print(f"      Boxscore != Pitcher")
        if boxscore_pks != outlook_pks:
            print(f"      Boxscore != Outlook")

print(f"\n{'='*60}")
print(f"SUMMARY:")
print(f"  Total files: {len(boxscore_files)}")
print(f"  Perfectly aligned: {aligned_files}")
print(f"  Misaligned: {len(misaligned_files)}")
print(f"  Success rate: {aligned_files/len(boxscore_files)*100:.2f}%")

if len(misaligned_files) == 0:
    print(f"\n🎉 ALL FILES PERFECTLY ALIGNED! 🎉")
else:
    print(f"\n⚠️  {len(misaligned_files)} files need attention")

print("="*60)

# Check for game_pk column presence
print("\nVerifying game_pk column in outlook files...")
sample_outlook = pd.read_csv(outlook_files[0])
if 'game_pk' in sample_outlook.columns:
    col_index = list(sample_outlook.columns).index('game_pk')
    print(f"  ✓ game_pk column present at index {col_index}")
else:
    print(f"  ✗ game_pk column missing!")
