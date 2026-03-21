import pandas as pd
import numpy as np

print("=" * 80)
print("Cleaning Final Dataset")
print("=" * 80)

# Load dataset
input_file = 'data/2025_dataset/2025_dataset.csv'
print(f"\nLoading {input_file}...")
df = pd.read_csv(input_file)
print(f"  Original: {len(df)} rows, {len(df.columns)} columns")

# Find and remove WAR columns
war_cols = [col for col in df.columns if 'war' in col.lower()]
print(f"\nRemoving {len(war_cols)} WAR columns:")
for col in war_cols:
    print(f"  - {col}")

df = df.drop(columns=war_cols)
print(f"\n  After removal: {len(df)} rows, {len(df.columns)} columns")

# Round all numeric columns to 2 decimal places
print("\nRounding numeric columns to 2 decimal places...")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
print(f"  Found {len(numeric_cols)} numeric columns")

for col in numeric_cols:
    df[col] = df[col].round(2)

print(f"  ✓ Rounded all numeric values to 2 decimals")

# Save cleaned dataset
output_file = 'data/2025_dataset/2025_dataset.csv'
print(f"\nSaving cleaned dataset to {output_file}...")
df.to_csv(output_file, index=False)
print("✅ Done!")

# Summary
print(f"\nFinal dataset:")
print(f"  Rows: {len(df):,}")
print(f"  Columns: {len(df.columns):,}")
print(f"  File: {output_file}")

# Show sample
print(f"\n📊 Sample (first 3 rows, columns 1-8):")
print(df.iloc[:3, :8].to_string(index=False))
