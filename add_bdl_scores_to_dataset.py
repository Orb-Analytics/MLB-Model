import pandas as pd

print("="*60)
print("Adding BDL Scores to 2025 Dataset")
print("="*60)

# First, restore original dataset
print("\n1. Restoring original dataset...")
import subprocess
subprocess.run(['python', '/workspaces/MLB-Model/create_final_dataset.py'], check=True)
subprocess.run(['python', '/workspaces/MLB-Model/clean_final_dataset.py'], check=True)

print("\n2. Loading files...")
dataset = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv')
bdl = pd.read_csv('/workspaces/MLB-Model/data/bdl_data/2025_bdl_dataset_with_duplicates.csv')

print(f"   Dataset: {len(dataset):,} rows, {len(dataset.columns)} columns")
print(f"   BDL: {len(bdl):,} rows, {len(bdl.columns)} columns")

# Verify alignment
print("\n3. Verifying alignment...")
assert len(dataset) == len(bdl), f"Row count mismatch: {len(dataset)} vs {len(bdl)}"
print(f"   ✓ Both files have {len(dataset):,} rows")

print("\n4. Checking score availability in BDL dataset...")
print(f"   Non-null home scores: {bdl['home_team_score'].notna().sum():,}")
print(f"   Non-null away scores: {bdl['away_team_score'].notna().sum():,}")

# Since both files align perfectly row-by-row, directly copy the scores
print("\n5. Copying scores (files align perfectly row-by-row)...")

# Verify alignment by checking a few key fields
sample_check = dataset.head(10).merge(
    bdl[['id', 'date', 'home_team_abbreviation', 'away_team_abbreviation']].head(10),
    left_on=['balldontlie_game_id', 'date', 'home_team_abbreviation', 'away_team_abbreviation'],
    right_on=['id', 'date', 'home_team_abbreviation', 'away_team_abbreviation'],
    how='inner'
)

if len(sample_check) == 10:
    print("   ✓ Alignment verified on sample")
else:
    print(f"   ⚠️ Warning: Sample alignment check returned {len(sample_check)} rows (expected 10)")

# Directly assign scores (since rows align perfectly)
merged = dataset.copy()
merged['home_team_score'] = bdl['home_team_score'].values
merged['away_team_score'] = bdl['away_team_score'].values

print(f"   Scores copied: {len(merged):,} rows")

if len(merged) != len(dataset):
    print(f"   ⚠️ WARNING: Row count changed from {len(dataset):,} to {len(merged):,}")
else:
    print(f"   ✓ Row count preserved")

# Check coverage
scores_available = merged['home_team_score'].notna().sum()
print(f"   Games with scores: {scores_available:,} ({scores_available/len(merged)*100:.1f}%)")

# Reorder columns: place scores after away_team_abbreviation
print("\n6. Reordering columns...")
cols = list(merged.columns)
away_abbr_idx = cols.index('away_team_abbreviation')

# New order: everything up to away_team_abbreviation, then scores, then rest
new_cols = (
    cols[:away_abbr_idx + 1] +  # Up to and including away_team_abbreviation
    ['home_team_score', 'away_team_score'] +  # Score columns
    [col for col in cols[away_abbr_idx + 1:] if col not in ['home_team_score', 'away_team_score']]
)

merged = merged[new_cols]

print(f"   Column order (first 10): {new_cols[:10]}")

# Save
output_path = '/workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv'
print(f"\n7. Saving to {output_path}...")
merged.to_csv(output_path, index=False)

print("\n" + "="*60)
print("✅ COMPLETE")
print("="*60)
print(f"Rows: {len(merged):,}")
print(f"Columns: {len(merged.columns)} (was {len(dataset.columns)})")
print(f"Added: home_team_score, away_team_score")
print(f"Position: After away_team_abbreviation (columns 6-7)")
print(f"Coverage: {scores_available:,} games ({scores_available/len(merged)*100:.1f}%)")

# Show sample
print("\nSample (first 5 games with scores):")
sample = merged[merged['home_team_score'].notna()].head(5)
print(sample[['date', 'home_team_abbreviation', 'away_team_abbreviation', 'home_team_score', 'away_team_score']].to_string(index=False))
