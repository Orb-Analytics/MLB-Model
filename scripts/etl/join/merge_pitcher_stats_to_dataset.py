"""
Merge starting pitcher standardized stats into main dataset.
Place computed features (entering, l10, l5) right after their corresponding raw stats.
"""

import pandas as pd
import re

# Load both files
print("Loading datasets...")
main_df = pd.read_csv('data/bdl_data/2025_bdl_dataset_with_duplicates.csv')
pitcher_df = pd.read_csv('data/bdl_data/starting_pitcher_standardized_stats.csv')

print(f"Main dataset: {len(main_df)} rows x {len(main_df.columns)} columns")
print(f"Pitcher stats: {len(pitcher_df)} rows x {len(pitcher_df.columns)} columns")

# Dedupe pitcher_df on balldontlie_game_id (keep first) to avoid creating extra duplicates
pitcher_df_deduped = pitcher_df.drop_duplicates(subset=['balldontlie_game_id'], keep='first')
print(f"Pitcher stats after deduplication: {len(pitcher_df_deduped)} rows")

# Merge on game ID
# Main dataset uses 'id', pitcher uses 'balldontlie_game_id'
merged_df = main_df.merge(
    pitcher_df_deduped.drop(columns=['date']),  # Drop date since it's already in main
    left_on='id',
    right_on='balldontlie_game_id',
    how='left'
)

print(f"\nAfter merge: {len(merged_df)} rows x {len(merged_df.columns)} columns")

# Drop the duplicate balldontlie_game_id column (we already have 'id')
if 'balldontlie_game_id' in merged_df.columns:
    merged_df = merged_df.drop(columns=['balldontlie_game_id'])

# Now intelligently reorder columns to place computed features near raw features
print("\nReordering columns...")

def get_base_feature_name(col):
    """Extract the base feature name without _entering, _l10, _l5 suffixes"""
    col_clean = col.replace('_entering', '').replace('_l10', '').replace('_l5', '')
    return col_clean

def create_smart_column_order(df):
    """
    Create column order that places computed features right after their raw counterparts.
    For example: home_starter_pitching_era, away_starter_pitching_era,
                 home_starter_pitching_era_entering, away_starter_pitching_era_entering,
                 home_starter_pitching_era_l10, away_starter_pitching_era_l10,
                 home_starter_pitching_era_l5, away_starter_pitching_era_l5
    """
    
    all_cols = list(df.columns)
    ordered_cols = []
    processed = set()
    
    # First, add non-starter columns (up to where starter columns begin)
    starter_idx = None
    for i, col in enumerate(all_cols):
        if 'home_starter_' in col or 'away_starter_' in col:
            starter_idx = i
            break
        ordered_cols.append(col)
        processed.add(col)
    
    # Now process starter columns intelligently
    # Group by base feature
    starter_cols = [col for col in all_cols if col not in processed]
    
    # Find unique base features (without home_/away_ prefix)
    unique_features = set()
    for col in starter_cols:
        if col.startswith('home_starter_'):
            base = col.replace('home_starter_', '')
            base = get_base_feature_name(base)
            unique_features.add(base)
        elif col.startswith('away_starter_'):
            base = col.replace('away_starter_', '')
            base = get_base_feature_name(base)
            unique_features.add(base)
    
    # Sort features (put 'id' first if it exists)
    sorted_features = sorted(unique_features)
    if 'id' in sorted_features:
        sorted_features.remove('id')
        sorted_features.insert(0, 'id')
    
    # For each feature, add columns in the order: raw, _entering, _l10, _l5
    for feature in sorted_features:
        # Check if this feature has raw values (no suffix)
        home_raw = f'home_starter_{feature}'
        away_raw = f'away_starter_{feature}'
        
        # Add raw columns first (if they exist)
        if home_raw in starter_cols and home_raw not in processed:
            ordered_cols.append(home_raw)
            processed.add(home_raw)
        if away_raw in starter_cols and away_raw not in processed:
            ordered_cols.append(away_raw)
            processed.add(away_raw)
        
        # Then add computed versions in order: _entering, _l10, _l5
        for suffix in ['_entering', '_l10', '_l5']:
            home_computed = f'home_starter_{feature}{suffix}'
            away_computed = f'away_starter_{feature}{suffix}'
            
            if home_computed in starter_cols and home_computed not in processed:
                ordered_cols.append(home_computed)
                processed.add(home_computed)
            if away_computed in starter_cols and away_computed not in processed:
                ordered_cols.append(away_computed)
                processed.add(away_computed)
    
    # Add any remaining columns that weren't processed
    for col in all_cols:
        if col not in processed:
            ordered_cols.append(col)
    
    return ordered_cols

# Create smart column order
ordered_cols = create_smart_column_order(merged_df)
merged_df = merged_df[ordered_cols]

print(f"Reordered to {len(ordered_cols)} columns")

# Save the merged dataset
output_path = 'data/bdl_data/2025_bdl_dataset_with_duplicates.csv'
merged_df.to_csv(output_path, index=False)

print(f"\n✓ Saved merged dataset: {output_path}")
print(f"  Final dimensions: {len(merged_df)} rows x {len(merged_df.columns)} columns")

# Show example of the new column ordering around ERA
print("\n" + "="*80)
print("EXAMPLE: ERA Column Grouping")
print("="*80)

era_cols = [col for col in merged_df.columns if 'pitching_era' in col and 'starter' in col]
print("\nColumns containing 'pitching_era':")
for i, col in enumerate(era_cols, 1):
    # Find the position in full column list
    pos = ordered_cols.index(col) + 1
    print(f"  {pos:3d}. {col}")

print("\n✓ Merge complete!")
