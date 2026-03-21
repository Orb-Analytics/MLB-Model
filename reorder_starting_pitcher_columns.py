import pandas as pd

print("Reordering columns in 2025_starting_pitchers.csv...")
print("=" * 80)

# Load the file
input_file = 'data/2025_dataset/joining/2025_starting_pitchers.csv'
df = pd.read_csv(input_file)

print(f"Original columns: {len(df.columns)}")

# Get all columns as a list
cols = df.columns.tolist()

# Columns 1-51 are already alternating (or neutral like ID, date)
# Columns 52-65 (index 51-64) need reordering - currently grouped home then away
# Columns 66-87 (index 65+) are already alternating

# The computed columns that need reordering (indices 51-64)
home_computed = cols[51:58]  # indices 51-57
away_computed = cols[58:65]  # indices 58-64

print(f"\nComputed columns to reorder:")
print(f"  Home (indices 51-57): {home_computed}")
print(f"  Away (indices 58-64): {away_computed}")

# Create new column order
new_cols = cols[:51]  # Keep columns 0-50 (indices 0-50)

# Interleave home and away computed columns
for home_col, away_col in zip(home_computed, away_computed):
    new_cols.append(home_col)
    new_cols.append(away_col)

# Add the remaining columns (rolling stats, indices 65+)
new_cols.extend(cols[65:])

print(f"\nNew column count: {len(new_cols)}")
print(f"\nColumns 52-66 (reordered to alternate):")
for i, col in enumerate(new_cols[51:66], 52):
    marker = '🏠' if 'home' in col else '✈️'
    print(f"  {i}. {marker} {col}")

# Reorder the dataframe
df_reordered = df[new_cols]

# Verify row count unchanged
assert len(df_reordered) == len(df), "Row count changed!"
assert len(df_reordered.columns) == len(df.columns), "Column count changed!"

# Save back to the same file
df_reordered.to_csv(input_file, index=False)

print(f"\n✅ Columns reordered and saved to {input_file}")
print(f"   Rows: {len(df_reordered)}")
print(f"   Columns: {len(df_reordered.columns)}")

# Show sample of the reordering
print(f"\n📊 Sample verification - columns are now alternating:")
sample_cols = new_cols[50:70]
for i, col in enumerate(sample_cols, 51):
    marker = '🏠' if 'home' in col else ('✈️' if 'away' in col else '📋')
    print(f"  {i}. {marker} {col}")
