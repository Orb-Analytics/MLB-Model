import pandas as pd
import glob
import numpy as np

print("Loading 2025_dataset.csv...")
dataset = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv')
print(f"  Dataset: {len(dataset):,} rows, {len(dataset.columns)} columns")

# Team name mapping to abbreviations
TEAM_NAME_TO_ABB = {
    'Arizona Diamondbacks': 'ARI',
    'Atlanta Braves': 'ATL',
    'Baltimore Orioles': 'BAL',
    'Boston Red Sox': 'BOS',
    'Chicago Cubs': 'CHC',
    'Chicago White Sox': 'CWS',
    'Cincinnati Reds': 'CIN',
    'Cleveland Guardians': 'CLE',
    'Colorado Rockies': 'COL',
    'Detroit Tigers': 'DET',
    'Houston Astros': 'HOU',
    'Kansas City Royals': 'KC',
    'Los Angeles Angels': 'LAA',
    'Los Angeles Dodgers': 'LAD',
    'Miami Marlins': 'MIA',
    'Milwaukee Brewers': 'MIL',
    'Minnesota Twins': 'MIN',
    'New York Mets': 'NYM',
    'New York Yankees': 'NYY',
    'Oakland Athletics': 'OAK',
    'Philadelphia Phillies': 'PHI',
    'Pittsburgh Pirates': 'PIT',
    'San Diego Padres': 'SD',
    'San Francisco Giants': 'SF',
    'Seattle Mariners': 'SEA',
    'St. Louis Cardinals': 'STL',
    'Tampa Bay Rays': 'TB',
    'Texas Rangers': 'TEX',
    'Toronto Blue Jays': 'TOR',
    'Washington Nationals': 'WSH'
}

print("\nLoading game-scores files...")
score_files = sorted(glob.glob('/workspaces/MLB-Model/data/game-scores/game_scores_*.csv'))
print(f"  Found {len(score_files)} files")

# Load all score files
all_scores = []
for file in score_files:
    df = pd.read_csv(file)
    all_scores.append(df)

scores_df = pd.concat(all_scores, ignore_index=True)
print(f"  Total score records: {len(scores_df):,}")

# Map team names to abbreviations
scores_df['home_team_abbr'] = scores_df['Home Team'].map(TEAM_NAME_TO_ABB)
scores_df['away_team_abbr'] = scores_df['Away Team'].map(TEAM_NAME_TO_ABB)

# Check for any unmapped teams
unmapped_home = scores_df[scores_df['home_team_abbr'].isna()]['Home Team'].unique()
unmapped_away = scores_df[scores_df['away_team_abbr'].isna()]['Away Team'].unique()

if len(unmapped_home) > 0 or len(unmapped_away) > 0:
    print("\n⚠️  Warning: Unmapped team names found:")
    if len(unmapped_home) > 0:
        print(f"  Home teams: {list(unmapped_home)}")
    if len(unmapped_away) > 0:
        print(f"  Away teams: {list(unmapped_away)}")

# Rename columns for clarity
scores_df = scores_df.rename(columns={
    'Date': 'date',
    'Home Score': 'home_team_score',
    'Away Score': 'away_team_score'
})

# Select relevant columns
scores_df = scores_df[['date', 'home_team_abbr', 'away_team_abbr', 'home_team_score', 'away_team_score']]

# Remove rows with missing abbreviations
scores_df = scores_df.dropna(subset=['home_team_abbr', 'away_team_abbr'])

print(f"  After mapping: {len(scores_df):,} valid score records")

# Merge with dataset
print("\nMerging scores with dataset...")
print("  Merging on: date, home_team_abbreviation, away_team_abbreviation")

# Check for duplicates in scores_df
score_dupes = scores_df.duplicated(subset=['date', 'home_team_abbr', 'away_team_abbr'], keep=False)
if score_dupes.any():
    print(f"\n⚠️  Warning: {score_dupes.sum()} duplicate score records found")
    dupes = scores_df[score_dupes].sort_values(['date', 'home_team_abbr'])
    print(dupes[['date', 'home_team_abbr', 'away_team_abbr', 'home_team_score', 'away_team_score']].head(20))

# Merge
merged = dataset.merge(
    scores_df,
    left_on=['date', 'home_team_abbreviation', 'away_team_abbreviation'],
    right_on=['date', 'home_team_abbr', 'away_team_abbr'],
    how='left'
)

# Drop the duplicate abbreviation columns from the merge
merged = merged.drop(columns=['home_team_abbr', 'away_team_abbr'])

print(f"  After merge: {len(merged):,} rows")

# Check how many games have scores
games_with_scores = merged['home_team_score'].notna().sum()
games_without_scores = merged['home_team_score'].isna().sum()

print(f"\n  Games with scores: {games_with_scores:,} ({games_with_scores/len(merged)*100:.1f}%)")
print(f"  Games without scores: {games_without_scores:,} ({games_without_scores/len(merged)*100:.1f}%)")

if games_without_scores > 0:
    print("\n  Sample of games without scores:")
    missing = merged[merged['home_team_score'].isna()][['date', 'home_team_abbreviation', 'away_team_abbreviation']].head(10)
    print(missing.to_string(index=False))

# Reorder columns to place scores after team abbreviations
print("\nReordering columns...")

# Find the position of away_team_abbreviation
cols = list(merged.columns)
away_team_abbr_idx = cols.index('away_team_abbreviation')

# Create new column order: everything up to and including away_team_abbreviation, 
# then the two score columns, then everything else
new_cols = (
    cols[:away_team_abbr_idx + 1] +  # Up to and including away_team_abbreviation
    ['home_team_score', 'away_team_score'] +  # Score columns
    [col for col in cols if col not in ['away_team_abbreviation', 'home_team_score', 'away_team_score'] 
     and cols.index(col) > away_team_abbr_idx]  # Everything after away_team_abbreviation
)

merged = merged[new_cols]

print(f"  New column order (first 10): {new_cols[:10]}")

# Save the updated dataset
output_path = '/workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv'
print(f"\nSaving updated dataset to {output_path}...")
merged.to_csv(output_path, index=False)

print("\n✅ Done!")
print(f"   Rows: {len(merged):,}")
print(f"   Columns: {len(merged.columns)} (was {len(dataset.columns)})")
print(f"   Added columns: home_team_score, away_team_score")
print(f"   Position: After away_team_abbreviation")
