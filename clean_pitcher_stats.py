#!/usr/bin/env python3
"""
Clean starting pitcher standardized stats:
1. Round all numeric columns to 2 decimal places
2. Fill NaN values with 0
"""

import pandas as pd
import numpy as np

print("="*80)
print("CLEANING STARTING PITCHER STANDARDIZED STATS")
print("="*80)

# Load the file
df = pd.read_csv('data/bdl_data/starting_pitcher_standardized_stats.csv')
print(f"\nLoaded: {len(df)} rows × {len(df.columns)} columns")

# Count NaN values before
nan_count_before = df.isna().sum().sum()
print(f"NaN values before: {nan_count_before}")

# Identify numeric columns (exclude ID and date columns)
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
non_numeric_cols = [col for col in df.columns if col not in numeric_cols]

print(f"\nNumeric columns to process: {len(numeric_cols)}")
print(f"Non-numeric columns (will not change): {len(non_numeric_cols)}")

# Round all numeric columns to 2 decimal places
for col in numeric_cols:
    df[col] = df[col].round(2)

print("\n✓ Rounded all numeric columns to 2 decimal places")

# Fill NaN values with 0
df = df.fillna(0)

# Count NaN values after
nan_count_after = df.isna().sum().sum()
print(f"\n✓ Filled NaN values with 0")
print(f"NaN values after: {nan_count_after}")
print(f"Values filled: {nan_count_before - nan_count_after}")

# Save the cleaned file
output_path = 'data/bdl_data/starting_pitcher_standardized_stats.csv'
df.to_csv(output_path, index=False)

print(f"\n✓ Saved cleaned file: {output_path}")

# Show sample of cleaned data
print("\n" + "="*80)
print("SAMPLE OF CLEANED DATA")
print("="*80)

print("\nFirst 5 rows, first 10 columns:")
print(df.head(5).iloc[:, :10])

# Show some feature columns to verify rounding
print("\nSample feature columns (showing rounding):")
sample_features = [
    'home_starter_pitching_era_entering',
    'home_starter_pitching_era_l5',
    'home_starter_pitching_whip_entering',
    'home_starter_k_bb_ratio_entering'
]

for feat in sample_features:
    if feat in df.columns:
        print(f"\n{feat}:")
        print(f"  First 10 values: {df[feat].head(10).tolist()}")

print("\n" + "="*80)
print("✓✓✓ CLEANING COMPLETE! ✓✓✓")
print("="*80)
print("\nChanges made:")
print("  ✓ All numeric values rounded to 2 decimal places")
print(f"  ✓ {nan_count_before} NaN values replaced with 0")
print("  ✓ Data types preserved (numeric columns stay numeric)")
print("="*80)
