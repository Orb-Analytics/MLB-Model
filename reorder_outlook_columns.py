import pandas as pd
import glob

print("="*60)
print("Reordering columns: moving game_pk to column 1")
print("="*60)

outlook_files = sorted(glob.glob('data/2011_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))

for outlook_file in outlook_files:
    df = pd.read_csv(outlook_file)
    
    # Get columns and reorder
    cols = df.columns.tolist()
    
    # Remove game_pk from wherever it is
    cols.remove('game_pk')
    
    # Insert game_pk at position 1 (after id which is at 0)
    cols.insert(1, 'game_pk')
    
    # Reorder dataframe
    df = df[cols]
    
    # Save back
    df.to_csv(outlook_file, index=False)

print(f"Processed {len(outlook_files)} files")

# Verify
sample = pd.read_csv(outlook_files[0])
print(f"\nNew column order (first 5):")
for i, col in enumerate(list(sample.columns)[:5]):
    print(f"  {i}: {col}")

print("\n✓ game_pk column moved to position 1")
