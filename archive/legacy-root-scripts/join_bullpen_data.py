import pandas as pd
import os

print("=" * 80)
print("Joining Bullpen Rolling Average Files")
print("=" * 80)

# Directory with rolling average files
rolling_dir = 'data/mlb_data/derived_stats/team_bullpen_derived_stats/'

# List of all rolling files to merge
rolling_files = [
    'bp_era_rolling.csv',
    'bp_whip_rolling.csv',
    'bp_k_per_9_rolling.csv',
    'bp_k_bb_ratio_rolling.csv',
    'bp_hr_per_9_rolling.csv',
    'bp_bb_per_9_rolling.csv'
]

print(f"\nLoading first file as base...")
first_file = os.path.join(rolling_dir, rolling_files[0])
df_result = pd.read_csv(first_file)
print(f"  {rolling_files[0]}")
print(f"  Rows: {len(df_result)}")
print(f"  Columns: {len(df_result.columns)}")

# Merge remaining files
print("\nMerging remaining files...")
for filename in rolling_files[1:]:
    filepath = os.path.join(rolling_dir, filename)
    print(f"  Merging {filename}...")
    
    # Load rolling file
    df_rolling = pd.read_csv(filepath)
    
    # Merge on game_pk
    df_result = pd.merge(
        df_result,
        df_rolling,
        on='game_pk',
        how='outer'
    )
    
    # Count columns added
    cols_added = len(df_rolling.columns) - 1  # -1 for game_pk
    print(f"    Added {cols_added} columns, total now: {len(df_result.columns)}")

print(f"\n✓ Final row count: {len(df_result)} rows")

# Summary
print(f"\nFinal dataset:")
print(f"  Total rows: {len(df_result)}")
print(f"  Total columns: {len(df_result.columns)}")

# Show all columns
rolling_cols = [col for col in df_result.columns if col != 'game_pk']
print(f"\n  Bullpen rolling average columns ({len(rolling_cols)}):")
for col in sorted(rolling_cols):
    non_null = df_result[col].notna().sum()
    print(f"    - {col:<45} ({non_null} non-null values)")

# Save to output file
output_file = 'data/2025_dataset/joining/2025_bullpen_stats.csv'
print(f"\nSaving to {output_file}...")
df_result.to_csv(output_file, index=False)
print("✅ Done!")

# Show sample
print(f"\n📊 Sample data (first 3 rows):")
display_cols = ['game_pk'] + sorted(rolling_cols)[:6]
print(df_result[display_cols].head(3).to_string(index=False))
