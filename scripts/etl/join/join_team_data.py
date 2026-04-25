import pandas as pd
import os

print("=" * 80)
print("Joining Team Stats with Rolling Averages")
print("=" * 80)

# Load base team_season_stats.csv
base_file = 'data/bdl_data/team_season_stats.csv'
print(f"\nLoading base {base_file}...")
df_base = pd.read_csv(base_file)
print(f"  Rows: {len(df_base)}")
print(f"  Columns: {len(df_base.columns)}")

# Directory with rolling average files
rolling_dir = 'data/mlb_data/derived_stats/team_derived_stats/'

# List of all rolling files to merge
rolling_files = [
    'batting_avg_rolling.csv',
    'batting_bb_per_g_rolling.csv',
    'batting_hr_per_g_rolling.csv',
    'batting_k_pct_rolling.csv',
    'batting_obp_rolling.csv',
    'batting_ops_rolling.csv',
    'batting_r_per_g_rolling.csv',
    'batting_slg_rolling.csv',
    'fielding_e_per_g_rolling.csv',
    'pitching_era_rolling.csv',
    'pitching_hr_per_9_rolling.csv',
    'pitching_k_bb_ratio_rolling.csv',
    'pitching_qs_rate_rolling.csv',
    'pitching_whip_rolling.csv'
]

# Merge each rolling file
print("\nMerging rolling average files...")
df_result = df_base.copy()

for filename in rolling_files:
    filepath = os.path.join(rolling_dir, filename)
    print(f"  Merging {filename}...")
    
    # Load rolling file
    df_rolling = pd.read_csv(filepath)
    
    # Merge on game_pk (base 'id' = rolling 'game_pk')
    df_result = pd.merge(
        df_result,
        df_rolling,
        left_on='id',
        right_on='game_pk',
        how='left'
    )
    
    # Drop the duplicate game_pk column
    df_result = df_result.drop(columns=['game_pk'])
    
    # Count columns added
    cols_added = len(df_rolling.columns) - 1  # -1 for game_pk
    print(f"    Added {cols_added} columns, total now: {len(df_result.columns)}")

# Verify row count unchanged
assert len(df_result) == len(df_base), f"Row count changed: {len(df_base)} -> {len(df_result)}"
print(f"\n✓ Row count verified: {len(df_result)} rows")

# Summary
print(f"\nFinal dataset:")
print(f"  Total rows: {len(df_result)}")
print(f"  Total columns: {len(df_result.columns)}")

# Show rolling columns added
rolling_cols = [col for col in df_result.columns if 'rolling' in col]
print(f"\n  Rolling average columns added ({len(rolling_cols)}):")
for col in sorted(rolling_cols):
    non_null = df_result[col].notna().sum()
    print(f"    - {col:<45} ({non_null} non-null values)")

# Save to output file
output_file = 'data/2025_dataset/joining/2025_team_stats.csv'
print(f"\nSaving to {output_file}...")
df_result.to_csv(output_file, index=False)
print("✅ Done!")

# Show sample
print(f"\n📊 Sample data (first 3 rows, selected columns):")
sample_cols = ['id', 'date', 'home_team_abbreviation', 'away_team_abbreviation']
sample_cols += [col for col in rolling_cols if 'batting_avg' in col or 'pitching_era' in col][:4]
print(df_result[sample_cols].head(3).to_string(index=False))
