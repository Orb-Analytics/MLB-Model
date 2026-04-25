"""
Join starting pitcher stats with rolling average derived stats
"""

import pandas as pd
from pathlib import Path

# Input files
BASE_FILE = '/workspaces/MLB-Model/data/bdl_data/starting_pitcher_stats.csv'
ROLLING_DIR = Path('/workspaces/MLB-Model/data/mlb_data/derived_stats/starting_pitcher_derived_stats')
OUTPUT_DIR = Path('/workspaces/MLB-Model/data/2025_dataset/joining')
OUTPUT_FILE = OUTPUT_DIR / '2025_starting_pitchers.csv'

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("="*80)
    print("Joining Starting Pitcher Stats with Rolling Averages")
    print("="*80)
    
    # Load base file
    print("\nLoading base starting_pitcher_stats.csv...")
    df_base = pd.read_csv(BASE_FILE)
    print(f"  Rows: {len(df_base)}")
    print(f"  Columns: {len(df_base.columns)}")
    
    # Start with base dataframe
    df_combined = df_base.copy()
    
    # Load and merge each rolling average file
    rolling_files = [
        'era_rolling.csv',
        'whip_rolling.csv',
        'k_per_9_rolling.csv',
        'k_bb_ratio_rolling.csv',
        'ip_per_gs_rolling.csv',
        'hr_per_9_rolling.csv',
        'bb_per_9_rolling.csv'
    ]
    
    print("\nMerging rolling average files...")
    for filename in rolling_files:
        file_path = ROLLING_DIR / filename
        if not file_path.exists():
            print(f"  ⚠️  WARNING: {filename} not found, skipping...")
            continue
        
        print(f"  Merging {filename}...")
        df_rolling = pd.read_csv(file_path)
        
        # Drop 'date' column from rolling files if present (already in base)
        if 'date' in df_rolling.columns:
            df_rolling = df_rolling.drop(columns=['date'])
        
        # Merge on game_pk (base file uses 'id' as game_pk)
        df_combined = pd.merge(
            df_combined,
            df_rolling,
            left_on='id',
            right_on='game_pk',
            how='left'
        )
        
        # Drop duplicate game_pk column from merge
        if 'game_pk' in df_combined.columns:
            df_combined = df_combined.drop(columns=['game_pk'])
        
        print(f"    Added {len(df_rolling.columns) - 1} columns, total now: {len(df_combined.columns)}")
    
    # Verify row count
    if len(df_combined) != len(df_base):
        print(f"\n⚠️  WARNING: Row count changed! Base: {len(df_base)}, Combined: {len(df_combined)}")
    else:
        print(f"\n✓ Row count verified: {len(df_combined)} rows")
    
    # Show column summary
    print(f"\nFinal dataset:")
    print(f"  Total rows: {len(df_combined)}")
    print(f"  Total columns: {len(df_combined.columns)}")
    
    # List the rolling average columns added
    rolling_cols = [col for col in df_combined.columns if 'rolling' in col.lower()]
    print(f"\n  Rolling average columns added ({len(rolling_cols)}):")
    for col in sorted(rolling_cols):
        non_null = df_combined[col].notna().sum()
        print(f"    - {col:40} ({non_null} non-null values)")
    
    # Save to output
    print(f"\nSaving to {OUTPUT_FILE}...")
    df_combined.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done!")
    
    # Show sample
    print("\n📊 Sample data (first non-null rolling values):")
    sample = df_combined[df_combined['home_era_rolling_5'].notna()].head(3)
    print(f"\nColumns: id, date, home_starter_full_name, home_era_rolling_5, home_whip_rolling_5")
    for _, row in sample.iterrows():
        print(f"  {row['id']}, {row['date']}, {row['home_starter_full_name']}, "
              f"{row['home_era_rolling_5']:.2f}, {row['home_whip_rolling_5']:.2f}")


if __name__ == '__main__':
    main()
