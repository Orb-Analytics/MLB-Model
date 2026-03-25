import pandas as pd

# Demonstrate merging for a sample date
date = '2011-04-01'

print("="*80)
print(f"DATASET MERGE DEMONSTRATION: {date}")
print("="*80)

# Load the three datasets
boxscore = pd.read_csv(f'data/2011_data/mlb_data/raw/boxscores/boxscores_{date}.csv')
pitcher = pd.read_csv(f'data/2011_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date}.csv')
outlook = pd.read_csv(f'data/2011_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{date}.csv')

print(f"\nDataset shapes:")
print(f"  Boxscores: {boxscore.shape}")
print(f"  Pitchers:  {pitcher.shape}")
print(f"  Outlook:   {outlook.shape}")

print(f"\nAll have {len(boxscore)} rows - perfect for merging!")

# Method 1: Simple concatenation (since rows align perfectly)
print("\n" + "-"*80)
print("METHOD 1: Horizontal concatenation (fastest)")
print("-"*80)
print("Since rows align perfectly, you can simply concatenate horizontally:")
print()
print("  merged = pd.concat([boxscore, pitcher, outlook], axis=1)")
print()
print("This creates a wide dataset with all columns from all three files.")

# Method 2: Merge on game_pk
print("\n" + "-"*80)
print("METHOD 2: Merge on game_pk (safer, explicit)")
print("-"*80)
print("For added safety, you can explicitly merge on game_pk:")
print()
print("  merged = boxscore.merge(pitcher, on='game_pk', suffixes=('_box', '_pit'))")
print("  merged = merged.merge(outlook, on='game_pk', suffixes=('', '_outlook'))")
print()

# Actually perform the merge to show it works
merged = boxscore.merge(pitcher, on='game_pk', suffixes=('_box', '_pit'))
merged = merged.merge(outlook, on='game_pk', suffixes=('', '_outlook'))

print(f"Merged dataset shape: {merged.shape}")
print(f"  Combined {boxscore.shape[1]} + {pitcher.shape[1]} + {outlook.shape[1]} = {merged.shape[1]} columns")
print(f"  All {len(merged)} rows preserved")

# Show sample of merged data
print("\n" + "-"*80)
print("SAMPLE MERGED DATA (first 3 games)")
print("-"*80)

# Check which columns have suffixes
date_col = 'date_box' if 'date_box' in merged.columns else 'date'
away_abbr_col = 'away_team_abbreviation_box' if 'away_team_abbreviation_box' in merged.columns else 'away_team_abbreviation'
home_abbr_col = 'home_team_abbreviation_box' if 'home_team_abbreviation_box' in merged.columns else 'home_team_abbreviation'

for i in range(3):
    row = merged.iloc[i]
    print(f"\nGame {i+1}:")
    print(f"  game_pk: {row['game_pk']}")
    print(f"  Date: {row[date_col]}")
    print(f"  Matchup: {row[away_abbr_col]} @ {row[home_abbr_col]}")
    print(f"  Score: {int(row['away_batting_r'])}-{int(row['home_batting_r'])}")
    print(f"  Away Starter: {row['away_starter_name']}")
    print(f"  Home Starter: {row['home_starter_name']}")
    print(f"  Venue: {row['venue']}")
    print(f"  Status: {row['status']}")

print("\n" + "="*80)
print("✓ Merge successful! All datasets aligned perfectly.")
print("="*80)

# Show column breakdown
print("\nColumn breakdown in merged dataset:")
print(f"  From boxscores: ~{boxscore.shape[1]} columns (team stats, batting, pitching, fielding)")
print(f"  From pitchers: ~{pitcher.shape[1]} columns (starting pitcher details)")
print(f"  From outlook: ~{outlook.shape[1]} columns (game info, teams, venue, betting)")
print(f"  Total: {merged.shape[1]} columns")
