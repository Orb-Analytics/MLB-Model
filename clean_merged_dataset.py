#!/usr/bin/env python3
"""
Clean up the merged dataset by removing duplicate columns
"""

import pandas as pd

print("="*80)
print("CLEANING MERGED DATASET - REMOVING DUPLICATE COLUMNS")
print("="*80)

# Load the merged dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
print(f"\nLoaded dataset: {len(df)} rows × {len(df.columns)} columns")

# Find duplicate column names
col_counts = {}
for col in df.columns:
    col_counts[col] = col_counts.get(col, 0) + 1

duplicates = {col: count for col, count in col_counts.items() if count > 1}

if duplicates:
    print(f"\nFound {len(duplicates)} column names that appear multiple times:")
    for col, count in sorted(duplicates.items()):
        print(f"  '{col}' appears {count} times")
    
    # Pandas adds .1, .2, etc. to duplicate column names
    # Let's identify which columns are duplicates
    print("\nIdentifying duplicate columns...")
    
    # Group columns by their base name (removing .1, .2, etc.)
    import re
    column_groups = {}
    for col in df.columns:
        # Remove .1, .2, etc. from the end
        base_name = re.sub(r'\.\d+$', '', col)
        if base_name not in column_groups:
            column_groups[base_name] = []
        column_groups[base_name].append(col)
    
    # Find which columns have duplicates
    duplicate_groups = {base: cols for base, cols in column_groups.items() if len(cols) > 1}
    
    print(f"\nFound {len(duplicate_groups)} sets of duplicate columns:")
    for base, cols in sorted(duplicate_groups.items())[:20]:
        print(f"  {base}: {cols}")
    
    # Keep only the first occurrence of each duplicate column
    columns_to_drop = []
    for base, cols in duplicate_groups.items():
        # Keep the first, drop the rest
        columns_to_drop.extend(cols[1:])
    
    print(f"\nDropping {len(columns_to_drop)} duplicate columns...")
    df_clean = df.drop(columns=columns_to_drop)
    
    print(f"\nCleaned dataset: {len(df_clean)} rows × {len(df_clean.columns)} columns")
    print(f"Removed {len(columns_to_drop)} columns")
    
    # Save the cleaned dataset
    df_clean.to_csv('data/bdl_data/2025_bdl_dataset.csv', index=False)
    print(f"\n✓ Saved cleaned dataset: data/bdl_data/2025_bdl_dataset.csv")
    print(f"  Rows: {len(df_clean)}")
    print(f"  Columns: {len(df_clean.columns)}")
    
else:
    print("\n✓ No duplicate column names found")

print("\n" + "="*80)
print("FINAL DATASET SUMMARY")
print("="*80)

df_final = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
print(f"\nRows: {len(df_final)}")
print(f"Columns: {len(df_final.columns)}")
print(f"\nFirst 30 columns:")
for i, col in enumerate(df_final.columns[:30], 1):
    print(f"  {i:2d}. {col}")

print("\n✓✓✓ DATASET READY! ✓✓✓")
print("="*80)
