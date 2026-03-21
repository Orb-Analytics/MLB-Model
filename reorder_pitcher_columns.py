"""
Reorder starting pitcher columns to alternate home/away for each feature.
Pattern: home_starter_X, away_starter_X, home_starter_Y, away_starter_Y, etc.
"""

import pandas as pd

# Load the file
df = pd.read_csv('data/bdl_data/starting_pitcher_standardized_stats.csv')

print(f"Loaded: {len(df)} rows x {len(df.columns)} columns")

# Start with identifier columns and IDs
ordered_cols = ['balldontlie_game_id', 'date', 'home_starter_id', 'away_starter_id']

# Get all other columns (excluding the ones we've already placed)
feature_cols = [col for col in df.columns if col not in ordered_cols]

# Extract unique feature names (without home_ or away_ prefix)
home_cols = [col for col in feature_cols if col.startswith('home_starter_') and col != 'home_starter_id']
away_cols = [col for col in feature_cols if col.startswith('away_starter_') and col != 'away_starter_id']

# Get feature names (remove home_starter_ prefix)
feature_names = sorted(set([col.replace('home_starter_', '') for col in home_cols if col != 'home_starter_id']))

print(f"\nFound {len(feature_names)} unique features")
print(f"Total feature columns: {len(home_cols)} home + {len(away_cols)} away = {len(home_cols) + len(away_cols)}")

# Alternate home and away for each feature
for feature in feature_names:
    home_col = f'home_starter_{feature}'
    away_col = f'away_starter_{feature}'
    
    if home_col in df.columns:
        ordered_cols.append(home_col)
    if away_col in df.columns:
        ordered_cols.append(away_col)

# Reorder the dataframe
df_reordered = df[ordered_cols]

print(f"\nReordered columns: {len(ordered_cols)} total")

# Save the reordered file
df_reordered.to_csv('data/bdl_data/starting_pitcher_standardized_stats.csv', index=False)

print(f"\n✓ Saved reordered file")

# Show sample of new column order
print("\n" + "="*80)
print("SAMPLE OF NEW COLUMN ORDER (first 20 columns)")
print("="*80)
for i, col in enumerate(ordered_cols[:20], 1):
    print(f"{i:2d}. {col}")

print("\n✓ Column reordering complete!")
