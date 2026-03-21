"""
Clean team season standardized stats:
- Round all numeric columns to 2 decimal places
- Fill NaN values with 0
"""

import pandas as pd
import numpy as np

# Load the file
df = pd.read_csv('data/bdl_data/team_season_standardized_stats.csv')

print(f"Loaded: {len(df)} rows x {len(df.columns)} columns")
print(f"NaN values before: {df.isna().sum().sum()}")

# Identify numeric vs non-numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

print(f"\nNumeric columns: {len(numeric_cols)}")
print(f"Non-numeric columns: {len(non_numeric_cols)}")

# Round all numeric columns to 2 decimal places
for col in numeric_cols:
    df[col] = df[col].round(2)

print("\n✓ Rounded all numeric columns to 2 decimal places")

# Fill NaN values with 0
df = df.fillna(0)

print(f"✓ Filled NaN values with 0")
print(f"NaN values after: {df.isna().sum().sum()}")

# Save the cleaned file
df.to_csv('data/bdl_data/team_season_standardized_stats.csv', index=False)

print(f"\n✓ Saved cleaned file")

# Show sample
print("\n" + "="*80)
print("SAMPLE DATA")
print("="*80)
print("\nRow 100:")
sample_cols = ['date', 'home_batting_ops_entering', 'home_batting_ops_l5', 
               'home_pitching_era_entering', 'home_pitching_era_l5']
for col in sample_cols:
    if col in df.columns:
        print(f"  {col}: {df.iloc[100][col]}")

print("\nRow 1000:")
for col in sample_cols:
    if col in df.columns:
        print(f"  {col}: {df.iloc[1000][col]}")

# Check data types
print("\n" + "="*80)
print("DATA TYPES")
print("="*80)
print(df.dtypes.value_counts())

# Count zeros in key columns  
print("\n" + "="*80)
print("ZERO VALUE COUNTS (expected for early season games)")
print("="*80)

check_cols = ['home_batting_ops_entering', 'home_batting_ops_l5', 
              'home_pitching_era_l5', 'away_pitching_era_l10']

for col in check_cols:
    if col in df.columns:
        zero_count = (df[col] == 0).sum()
        print(f"{col}: {zero_count} / {len(df)} ({zero_count/len(df)*100:.1f}%)")

print("\n✓ Cleaning complete!")
