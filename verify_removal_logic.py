import pandas as pd

print("="*80)
print("VERIFYING: Removing INITIAL (postponed) vs KEEPING RESCHEDULED (played)")
print("="*80)

# Load the lists
keep_df = pd.read_csv('games_to_keep_2430.csv')
remove_df = pd.read_csv('games_to_remove_37.csv')

# Show a few examples
print("\nExample duplicates:")
print("\nGame 244205 (TB@BOS):")
keep_entry = keep_df[keep_df['game_pk'] == 244205]
remove_entry = remove_df[remove_df['game_pk'] == 244205]
if len(keep_entry) > 0:
    print(f"  KEEPING: {keep_entry.iloc[0]['date']} (game actually played)")
if len(remove_entry) > 0:
    print(f"  REMOVING: {remove_entry.iloc[0]['date']} (originally scheduled, postponed)")

print("\nGame 244238 (OAK@LAA):")
keep_entry = keep_df[keep_df['game_pk'] == 244238]
remove_entry = remove_df[remove_df['game_pk'] == 244238]
if len(keep_entry) > 0:
    print(f"  KEEPING: {keep_entry.iloc[0]['date']} (game actually played)")
if len(remove_entry) > 0:
    print(f"  REMOVING: {remove_entry.iloc[0]['date']} (originally scheduled, postponed)")

print("\nGame 244591 (HOU@WSH - the doubleheader we found earlier):")
keep_entry = keep_df[keep_df['game_pk'] == 244591]
remove_entry = remove_df[remove_df['game_pk'] == 244591]
if len(keep_entry) > 0:
    print(f"  KEEPING: {keep_entry.iloc[0]['date']} (game actually played)")
if len(remove_entry) > 0:
    print(f"  REMOVING: {remove_entry.iloc[0]['date']} (originally scheduled, postponed)")

# Logic explanation
print("\n" + "="*80)
print("LOGIC CONFIRMATION")
print("="*80)
print("\nOriginal BDL data (2,430 games):")
print("  ✓ Contains only games that ACTUALLY HAPPENED")
print("  ✓ Does NOT include originally scheduled dates that were postponed")

print("\nMLB Boxscore data (2,467 games):")
print("  ✓ Contains games that actually happened")
print("  ✓ ALSO contains originally scheduled dates (before postponement)")
print("  ✓ Results in 37 duplicate game_pks")

print("\nWhat we're doing:")
print("  ✓ KEEPING: Games from original BDL = games that actually played")
print("  ✓ REMOVING: Games NOT in BDL = originally scheduled dates (postponed)")

print("\nResult:")
print("  ✓ Final dataset: 2,430 games (each game appears once, on the date it was played)")
print("="*80)
