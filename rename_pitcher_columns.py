#!/usr/bin/env python3
"""
Rename derived pitcher columns to include 'starting_pitcher' in the name
"""

import pandas as pd

print("="*80)
print("RENAMING DERIVED PITCHER COLUMNS")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
print(f"\nLoaded dataset: {len(df)} rows × {len(df.columns)} columns")

# Define the derived stats that need to be renamed
derived_stats = [
    'k_bb_ratio',
    'qs_rate',
    'ip_per_gs',
    'hr_per_9',
    'bb_per_9',
    'h_per_9',
    'win_pct'
]

# Create the rename mapping
rename_mapping = {}

for prefix in ['home', 'away']:
    for stat in derived_stats:
        old_name = f'{prefix}_{stat}'
        new_name = f'{prefix}_starting_pitcher_{stat}'
        
        if old_name in df.columns:
            rename_mapping[old_name] = new_name

print(f"\nRenaming {len(rename_mapping)} columns:")
for old, new in sorted(rename_mapping.items()):
    print(f"  {old:<30} → {new}")

# Rename the columns
df = df.rename(columns=rename_mapping)

print(f"\n✓ All columns renamed successfully")

# Verify the new column names exist
print("\n" + "="*80)
print("VERIFICATION")
print("="*80)

print("\nNew starting pitcher derived columns:")
sp_derived_cols = [col for col in df.columns if 'starting_pitcher' in col and any(stat in col for stat in derived_stats)]
for col in sorted(sp_derived_cols):
    print(f"  ✓ {col}")

# Save the updated dataset
print("\n" + "="*80)
print("SAVING UPDATED DATASET")
print("="*80)

df.to_csv('data/bdl_data/2025_bdl_dataset.csv', index=False)
print(f"\n✓ Saved: data/bdl_data/2025_bdl_dataset.csv")
print(f"  Rows: {len(df)}")
print(f"  Columns: {len(df.columns)}")

print("\n✓✓✓ RENAMING COMPLETE! ✓✓✓")
print("="*80)
